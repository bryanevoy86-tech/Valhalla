from pydantic import BaseModel
import os, json

class Settings(BaseModel):
    database_url: str
    jwt_secret: str
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

    @classmethod
    def load(cls) -> "Settings":
        flags_env = os.environ.get("FEATURE_FLAGS_JSON", "{}")
        try:
            flags = json.loads(flags_env)
        except Exception:
            flags = {}
        return cls(
            database_url=os.environ.get("DATABASE_URL", ""),
            jwt_secret=os.environ.get("JWT_SECRET", "change-me"),
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
        )

settings = Settings.load()
