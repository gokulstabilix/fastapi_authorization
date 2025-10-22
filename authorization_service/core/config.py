from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the project root (python_project/) so .env is found regardless of CWD
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str 
    API_V1_STR: str 
    DATABASE_URL: str
    SECRET_KEY: str 
    ALGORITHM: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    BACKEND_CORS_ORIGINS:str

    # SMTP / Email
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 465
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_SSL: bool = True
    SMTP_USE_TLS: bool = False
    MAIL_FROM: str | None = None

    # Email OTP settings
    EMAIL_OTP_EXPIRE_MINUTES: int 
    EMAIL_OTP_LENGTH: int
    EMAIL_OTP_RESEND_INTERVAL_SECONDS: int
    EMAIL_OTP_MAX_ATTEMPTS: int
    
    # Redis settings for rate limiting
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    
    # Rate limiting settings (requests per minute)
    RATE_LIMIT_LOGIN: str 
    RATE_LIMIT_REFRESH: str 
    RATE_LIMIT_SEND_OTP: str 
    RATE_LIMIT_VERIFY_OTP: str 
    RATE_LIMIT_DEFAULT: str

    # Redis settings for caching
    REDIS_CACHE_EXPIRE_SECONDS: int

    # Database connection pooling
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

    # Minio settings
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), 
        env_file_encoding="utf-8", 
        case_sensitive=False,
        extra='ignore'
    )


settings = Settings()
