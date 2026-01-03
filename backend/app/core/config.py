from functools import lru_cache

from pydantic import AnyUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Valhalla API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    POSTGRES_SERVER: str | None = None
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None
    DATABASE_URL: AnyUrl | None = None
    REDIS_URL: str = "redis://redis:6379/0"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # --- Underwriting knobs ---
    UW_ASSIGNMENT_FEE_PCT: float = 0.08  # 8% of ARV default
    UW_TARGET_PROFIT: float = 25000.0  # target net profit ($)
    UW_FLIP_DISCOUNT_PCT: float = 0.70  # 70% rule baseline
    UW_SAFETY_BUFFER_PCT: float = 0.03  # 3% buffer on suggested offer

    # --- Webhooks / Email ---
    WEBHOOK_URLS_CSV: str | None = None  # "https://example.com/hook1,https://example.com/hook2"
    EMAIL_PROVIDER: str | None = "stub"  # "stub" | "sendgrid"
    SENDGRID_API_KEY: str | None = None
    EMAIL_FROM: str | None = "noreply@valhalla.local"

    # --- RQ / Background Jobs ---
    RQ_REDIS_URL: str | None = None  # fallback to REDIS_URL
    RQ_QUEUE_NAME: str = "default"

    # --- S3 / MinIO ---
    S3_ENDPOINT_URL: str | None = "http://minio:9000"
    S3_REGION: str | None = "us-east-1"
    S3_ACCESS_KEY: str | None = "minioadmin"
    S3_SECRET_KEY: str | None = "minioadmin"
    S3_BUCKET: str | None = "valhalla"
    S3_FORCE_PATH_STYLE: bool = True  # MinIO needs this
    S3_PRESIGN_EXPIRE_SEC: int = 900  # 15 minutes

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
