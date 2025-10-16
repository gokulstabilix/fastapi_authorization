from typing import Optional, List, Dict, Any, Callable, Awaitable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
import logging
import time
from starlette.types import ASGIApp, Receive, Scope, Send
from authorization_service.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = None

# Default rate limits in requests per minute
DEFAULT_RATE_LIMITS = {
    "auth_login": "30/minute",
    "auth_refresh": "60/minute",
    "auth_send_otp": "5/minute",
    "auth_verify_otp": "10/minute",
}

def get_redis_client():
    global redis_client
    if redis_client is None or not redis_client.ping(): # Added check for redis_client.ping()
        try:
            # You can customize Redis connection settings here
            redis_client = redis.Redis(
                host=settings.REDIS_HOST if hasattr(settings, 'REDIS_HOST') else 'localhost',
                port=settings.REDIS_PORT if hasattr(settings, 'REDIS_PORT') else 6379,
                db=0,
                decode_responses=True
            )
            # Test the connection
            redis_client.ping()
            logger.info("Connected to Redis for rate limiting")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for rate limiting: {e}")
            # Fallback to in-memory storage if Redis is not available
            redis_client = None
    return redis_client

# Initialize the rate limiter with in-memory storage by default
# We'll update the storage later if Redis is available
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"
)

def get_limiter_key(request: Request) -> str:
    """
    Generate a unique key for rate limiting based on the endpoint and user IP.
    """
    endpoint = request.url.path
    # Get the first path part after /api/v1/
    parts = endpoint.split('/')
    if len(parts) > 3 and parts[1] == 'api' and parts[2].startswith('v'):
        # For API endpoints, use the first part after /api/v1/ as the key
        return f"rl:{parts[3] if len(parts) > 3 else 'default'}:{get_remote_address(request)}"
    # For non-API endpoints, use the first path part
    return f"rl:{parts[1] if len(parts) > 1 else 'root'}:{get_remote_address(request)}"

def get_rate_limit_for_endpoint(endpoint: str) -> str:
    """
    Get the rate limit for a specific endpoint.
    """
    # Extract the endpoint key (e.g., 'auth_login' from '/api/v1/auth/login')
    parts = endpoint.strip('/').split('/')
    if len(parts) >= 2 and parts[0] == 'api' and parts[1].startswith('v'):
        # For API endpoints, use the first part after /api/v1/
        endpoint_key = parts[2] if len(parts) > 2 else 'default'
    else:
        # For non-API endpoints, use the first path part
        endpoint_key = parts[0] if parts else 'root'
    
    # Check if we have a specific rate limit for this endpoint
    for key, limit in DEFAULT_RATE_LIMITS.items():
        if key.startswith(endpoint_key):
            return limit
    
    # Default rate limit
    return "100/minute"

def init_rate_limiter(app):
    """
    Initialize rate limiting for the FastAPI application.
    """
    global limiter
    try:
        redis_client = get_redis_client()
        if redis_client:
            limiter.storage_uri = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
            logger.info("Using Redis for rate limiting")
        else:
            limiter.storage_uri = "memory://"
            logger.info("Using in-memory storage for rate limiting (Redis not available)")
    except Exception as e:
        logger.warning(f"Failed to initialize Redis, falling back to in-memory storage: {e}")
        limiter.storage_uri = "memory://" # Ensure fallback even if error during init
    
    app.state.limiter = limiter
    
    @app.exception_handler(RateLimitExceeded)
    async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
        try:
            rate_limit = request.state.limiter.current_limit
            headers = {
                "Retry-After": str(int(exc.retry_after)) if exc.retry_after else None,
                "X-RateLimit-Limit": str(rate_limit.limit) if hasattr(rate_limit, 'limit') else None,
                "X-RateLimit-Remaining": str(rate_limit.remaining) if hasattr(rate_limit, 'remaining') else None,
                "X-RateLimit-Reset": str(int(rate_limit.reset_at.timestamp())) if hasattr(rate_limit, 'reset_at') and rate_limit.reset_at else None,
            }
            logger.warning(f"Rate limit exceeded: {exc.detail}")
            retry_after = int(exc.retry_after) if exc.retry_after else 60
            friendly_message = (
                "Too many requests. Please try again after "
                f"{retry_after} seconds. "
                f"Current rate limit: {exc.detail}"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": friendly_message,
                    "retry_after_seconds": retry_after,
                    "rate_limit": exc.detail
                },
                headers={k: v for k, v in headers.items() if v is not None},
            )
        except Exception as e:
            logger.error(f"Error in rate limit handler: {e}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please try again later."}
            )
    
    @app.middleware("http")
    async def add_rate_limit_headers(request: Request, call_next):
        try:
            response = await call_next(request)
            if hasattr(request.state, "limiter") and hasattr(request.state.limiter, "current_limit"):
                headers = {
                    "X-RateLimit-Limit": str(request.state.limiter.current_limit.limit),
                    "X-RateLimit-Remaining": str(request.state.limiter.current_limit.remaining),
                    "X-RateLimit-Reset": str(int(request.state.limiter.current_limit.reset_at.timestamp())),
                }
                response.headers.update(headers)
            return response
        except Exception as e:
            logger.error(f"Error in rate limit middleware: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )
    
    logger.info("Rate limiting middleware initialized")

