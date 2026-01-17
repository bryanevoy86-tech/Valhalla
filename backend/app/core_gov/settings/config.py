from __future__ import annotations

import os
from pydantic import BaseModel

class Settings(BaseModel):
    # If set, protects sensitive endpoints with X-VALHALLA-KEY
    VALHALLA_DEV_KEY: str | None = None

    # CORS (comma-separated origins)
    CORS_ALLOWED_ORIGINS: list[str] = []

def load_settings() -> Settings:
    key = os.getenv("VALHALLA_DEV_KEY")
    cors_raw = os.getenv("CORS_ALLOWED_ORIGINS", "")
    origins = [o.strip() for o in cors_raw.split(",") if o.strip()]

    return Settings(
        VALHALLA_DEV_KEY=key,
        CORS_ALLOWED_ORIGINS=origins,
    )
