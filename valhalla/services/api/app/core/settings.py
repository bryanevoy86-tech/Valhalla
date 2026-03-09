from __future__ import annotations

import json
from typing import List, Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_origins(raw: str | None) -> List[str]:
    if not raw:
        return []
    s = raw.strip()
    if not s:
        return []

    # Try JSON list first: ["https://a","https://b"]
    if s.startswith("["):
        try:
            v = json.loads(s)
            if isinstance(v, list):
                return [str(x).strip() for x in v if str(x).strip()]
        except Exception:
            pass

    # Fallback: comma-separated: https://a,https://b
    return [p.strip() for p in s.split(",") if p.strip()]


class Settings(BaseSettings):
    # IMPORTANT: do not rely on .env files in Render containers
    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
    )

    # REQUIRED CORE
    database_url: str = Field(alias="DATABASE_URL")
    jwt_secret: str = Field(alias="VALHALLA_JWT_SECRET")
    env: str = "dev"
    
    # CORS (raw string from env, parse safely)
    cors_allowed_origins_raw: Optional[str] = Field(default=None, alias="CORS_ALLOWED_ORIGINS")

    # Optional / Feature-gated
    notify_url: str | None = None           # for SLA breach pings (Discord/Slack/Zapier)
    feature_flags: dict[str, bool] = {}
    
    # S3 Storage
    storage_provider: str = "s3"
    s3_bucket: str = ""
    s3_region: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    
    # DocuSign PowerForm
    docusign_powerform_url: str = ""
    
    # Sentry
    sentry_dsn: str = ""
    
    # Builder
    BUILDER_KEY: str = ""
    BUILDER_ALLOWED_DIRS: list[str] = [
        "services/api/app/routers",
        "services/api/app/models",
        "services/api/app/schemas",
        "services/api/jobs",
        "services/api/alembic/versions",
        "web/weweb-datasources",
        "web/weweb-widgets",
    ]
    BUILDER_MAX_FILE_BYTES: int = Field(default=200000)

    # Git auto-commit/push flags
    GIT_ENABLE_AUTOCOMMIT: bool = Field(default=False)
    GIT_REPO_DIR: str = Field(default="")
    GIT_REMOTE_NAME: str = Field(default="origin")
    GIT_BRANCH: str = Field(default="main")
    GIT_USER_NAME: str = Field(default="Heimdall Bot")
    GIT_USER_EMAIL: str = Field(default="heimdall-bot@valhalla.local")
    GITHUB_TOKEN: str = Field(default="")

    # --- Notifications ---
    DEFAULT_WEBHOOK_URL: str | None = None
    SMTP_HOST: str | None = Field(default=None, alias="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, alias="SMTP_PORT")
    SMTP_USER: str | None = Field(default=None, alias="SMTP_USER")
    SMTP_PASS: str | None = Field(default=None, alias="SMTP_PASS")
    SMTP_USERNAME: str | None = Field(default=None, alias="SMTP_USERNAME")
    SMTP_PASSWORD: str | None = Field(default=None, alias="SMTP_PASSWORD")
    SMTP_FROM: str | None = "noreply@valhalla.local"

    # Twilio SMS
    TWILIO_ACCOUNT_SID: str | None = Field(default=None)
    TWILIO_AUTH_TOKEN: str | None = Field(default=None)
    TWILIO_PHONE_NUMBER: str | None = Field(default=None)

    @model_validator(mode="after")
    def _smtp_backcompat(self):
        """Fallback: if SMTP_USER/PASS not set, use USERNAME/PASSWORD"""
        if not self.SMTP_USER and self.SMTP_USERNAME:
            self.SMTP_USER = self.SMTP_USERNAME
        if not self.SMTP_PASS and self.SMTP_PASSWORD:
            self.SMTP_PASS = self.SMTP_PASSWORD
        return self

    @property
    def cors_allowed_origins(self) -> List[str]:
        return _parse_origins(self.cors_allowed_origins_raw)


# singleton (import this everywhere)
settings = Settings()
