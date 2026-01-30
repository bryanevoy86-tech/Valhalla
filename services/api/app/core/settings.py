from pydantic import BaseModel, Field, model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os, json

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
        populate_by_name=True,
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
    CORS_ALLOWED_ORIGINS: list[str] = Field(default=[], validation_alias="CORS_ALLOWED_ORIGINS")
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
    DEFAULT_WEBHOOK_URL: str | None = Field(default=None)
    SMTP_HOST: str | None = Field(default=None, validation_alias="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, validation_alias="SMTP_PORT")
    SMTP_USER: str | None = Field(default=None, validation_alias="SMTP_USER")
    SMTP_PASS: str | None = Field(default=None, validation_alias="SMTP_PASS")
    SMTP_USERNAME: str | None = Field(default=None, validation_alias="SMTP_USERNAME")
    SMTP_PASSWORD: str | None = Field(default=None, validation_alias="SMTP_PASSWORD")
    SMTP_FROM: str | None = Field(default="noreply@valhalla.local")

    # Twilio SMS
    TWILIO_ACCOUNT_SID: str | None = Field(default=None)
    TWILIO_AUTH_TOKEN: str | None = Field(default=None)
    TWILIO_PHONE_NUMBER: str | None = Field(default=None)

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse comma-separated string to list, or return as-is if already a list"""
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()] if v else []
        if isinstance(v, list):
            return v
        return []

    @model_validator(mode="after")
    def _smtp_backcompat(self):
        """Fallback: if SMTP_USER/PASS not set, use USERNAME/PASSWORD"""
        if not self.SMTP_USER and self.SMTP_USERNAME:
            self.SMTP_USER = self.SMTP_USERNAME
        if not self.SMTP_PASS and self.SMTP_PASSWORD:
            self.SMTP_PASS = self.SMTP_PASSWORD
        return self

    @classmethod
    def load(cls) -> "Settings":
        flags_env = os.environ.get("FEATURE_FLAGS_JSON", "{}")
        try:
            flags = json.loads(flags_env)
        except Exception:
            flags = {}
        return cls(
            database_url=os.environ.get("DATABASE_URL", ""),
            jwt_secret=os.environ.get("VALHALLA_JWT_SECRET", "change-me"),
            env=os.environ.get("ENV", "dev"),
            notify_url=os.environ.get("NOTIFY_URL"),
            feature_flags=flags,
            storage_provider=os.environ.get("STORAGE_PROVIDER", "s3"),
            s3_bucket=os.environ.get("S3_BUCKET", ""),
            s3_region=os.environ.get("S3_REGION", ""),
            s3_access_key_id=os.environ.get("S3_ACCESS_KEY_ID", ""),
            s3_secret_access_key=os.environ.get("S3_SECRET_ACCESS_KEY", ""),
            docusign_powerform_url=os.environ.get("DOCUSIGN_POWERFORM_URL", ""),
            sentry_dsn=os.environ.get("SENTRY_DSN", ""),
            CORS_ALLOWED_ORIGINS=os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if os.environ.get("CORS_ALLOWED_ORIGINS") else [],
            HEIMDALL_BUILDER_API_KEY=os.environ.get("HEIMDALL_BUILDER_API_KEY", ""),
        )

settings = Settings.load()
