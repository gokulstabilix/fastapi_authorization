from fastapi import FastAPI, Request

from authorization_service.api.v1.api import api_router
from authorization_service.core.config import settings
from authorization_service.db.base import Base  # Import models
from authorization_service.db.session import engine
from authorization_service.utils.logger import logger
from authorization_service.utils.cors import setup_cors
from authorization_service.core.rate_limiter import init_rate_limiter, limiter


def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME)
    
    # Configure CORS
    setup_cors(app, allow_origins=settings.BACKEND_CORS_ORIGINS)
    
    # Initialize rate limiting
    init_rate_limiter(app)
    
    app.include_router(api_router, prefix=settings.API_V1_STR)

    logger.info("Starting application...")

    @app.on_event("startup")
    def startup_db_tables():
        try:
            # Create tables using the synchronous engine
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created")
        except Exception as e:
            logger.error(f"Could not connect to database: {e}")

    @app.get("/")
    def read_root():
        return {"status": "ok", "service": settings.PROJECT_NAME}

    return app


app = create_app()
