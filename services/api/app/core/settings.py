from pydantic import Field, model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os, json

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
    )

    database_url: str = Field(validation_alias="DATABASE_URL")
    jwt_secret: str = Field(validation_alias="VALHALLA_JWT_SECRET")
    env: str = "dev"
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
    # CORS
    CORS_ALLOWED_ORIGINS: str = Field(default="", validation_alias="CORS_ALLOWED_ORIGINS")
    # Builder
    HEIMDALL_BUILDER_API_KEY: str = ""
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
    SMTP_HOST: str | None = Field(default=None, validation_alias="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, validation_alias="SMTP_PORT")
    SMTP_USER: str | None = Field(default=None, validation_alias="SMTP_USER")
    SMTP_PASS: str | None = Field(default=None, validation_alias="SMTP_PASS")
    SMTP_USERNAME: str | None = Field(default=None, validation_alias="SMTP_USERNAME")
    SMTP_PASSWORD: str | None = Field(default=None, validation_alias="SMTP_PASSWORD")
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
    def cors_origins_list(self) -> list[str]:
        """
        Accept either:
        - JSON list string: ["https://a.com","https://b.com"]
        - Comma-separated string: https://a.com,https://b.com
        - Already a list (defensive)
        Never raises during Settings construction (prevents migration boot failure).
        """
        v = self.CORS_ALLOWED_ORIGINS

        if v is None:
            return []

        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]

        s = str(v).strip()
        if not s:
            return []

        # Try JSON first
        if s.startswith("["):
            try:
                data = json.loads(s)
                if isinstance(data, list):
                    return [str(x).strip() for x in data if str(x).strip()]
            except Exception:
                pass

        # Fallback: comma split
        return [x.strip() for x in s.split(",") if x.strip()]

    @classmethod
    def load(cls) -> "Settings":
        # Always load from environment via BaseSettings
        # (prevents accidental empty-dict construction that bypasses env vars)
        return cls()

settings = Settings.load()
