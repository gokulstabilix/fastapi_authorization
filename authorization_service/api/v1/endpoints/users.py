from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from authorization_service.api.deps import get_db, get_current_user
from authorization_service.schemas.user import UserCreate, UserRead
from authorization_service.services.user_service import UserService
from authorization_service.core.rate_limiter import get_redis_client
from authorization_service.core.config import settings
from authorization_service.utils.logger import logger

router = APIRouter()


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    users = UserService(db)
    try:
        user = users.register(user_in)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    # Send verification OTP after successful registration (best-effort)
    try:
        users.send_verification_otp(user.email)
    except Exception:
        # Do not fail user creation if email fails; client can trigger resend via /auth/send-otp
        pass
    return user


@router.get("/users/profile", response_model=UserRead)
def read_users_me(current_user=Depends(get_current_user)):
    redis_client = get_redis_client()
    user_id = str(current_user.id)
    cache_key = f"user_profile:{user_id}"

    if not redis_client:
        logger.warning("Redis client is not available for caching.")

    if redis_client:
        cached_profile = redis_client.get(cache_key)
        if cached_profile:
            logger.info(f"Cache hit for user profile: {user_id}")
            return UserRead.parse_raw(cached_profile)
        logger.info(f"Cache miss for user profile: {user_id}")

    # Fetch from database if not in cache or Redis is not available
    logger.info(f"Fetching user profile from DB for user: {user_id}")
    user_profile = current_user

    # Store in cache if Redis is available
    if redis_client and user_profile:
        # Convert SQLAlchemy model to Pydantic model for serialization
        user_read_profile = UserRead.from_orm(user_profile)
        redis_client.setex(cache_key, settings.REDIS_CACHE_EXPIRE_SECONDS, user_read_profile.json())
        logger.info(f"User profile for {user_id} stored in cache for {settings.REDIS_CACHE_EXPIRE_SECONDS} seconds")

    return user_profile
