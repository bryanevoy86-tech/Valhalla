from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    ENV: str = os.getenv("ENV", "prod")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Render injects PORT; we dont need it here but leaving for ref
    PORT: int = int(os.getenv("PORT", "8000"))

    # Database (Render Postgres or your own)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/valhalla"
    )

    # CORS
    CORS_ALLOWED_ORIGINS: List[str] = [
        o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()
    ] or [
        "https://valhalla.weweb-preview.io",
        "https://editor.weweb.io",
        "https://preview.weweb.io",
        "https://*.weweb.io",
    ]

    # Heimdall Builder flags
    HEIMDALL_BUILDER: str = os.getenv("HEIMDALL_BUILDER", "off")
    BUILDER_SAFE_MODE: str = os.getenv("BUILDER_SAFE_MODE", "on")
    AUTO_DEPLOY: str = os.getenv("AUTO_DEPLOY", "off")
    ALLOW_DESTRUCTIVE: str = os.getenv("ALLOW_DESTRUCTIVE", "off")

    HEIMDALL_BUILDER_API_KEY: str | None = os.getenv("HEIMDALL_BUILDER_API_KEY")

settings = Settings()
