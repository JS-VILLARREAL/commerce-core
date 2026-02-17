from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Product Management API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/product_db"
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PRODUCT_TTL: int = 300  # Cache TTL in seconds
    REDIS_REPORT_TTL: int = 600  # Cache TTL for reports in seconds

    # JWT settings
    JWT_SECRET_KEY: str = "your-256-bit-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Rate limiting settings
    RATE_LIMIT_PER_MINUTE: int = 60  # Max requests per minute per IP

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
