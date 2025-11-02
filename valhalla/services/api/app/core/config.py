from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    # Load from environment and optional .env; ignore unknown envs
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    ENV: str = "prod"
    DEBUG: bool = False
    PORT: int = 8000

    # Database (Render Postgres or local)
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/valhalla"

    # CORS as comma-separated string from env; parsed via helper
    CORS_ALLOWED_ORIGINS: str = ""

    # Builder flags
    HEIMDALL_BUILDER: str = "off"
    BUILDER_SAFE_MODE: str = "on"
    AUTO_DEPLOY: str = "off"
    ALLOW_DESTRUCTIVE: str = "off"
    HEIMDALL_BUILDER_API_KEY: str = ""

    # Builder guardrails
    BUILDER_ALLOWED_DIRS: List[str] = [
        "services/api/app/routers",
        "services/api/app/models",
        "services/api/app/schemas",
        "services/api/app/core",
        "services/api/alembic/versions",
        "services/worker",
        ".github/workflows",
    ]
    BUILDER_MAX_FILE_BYTES: int = 200000  # 200KB

    # Git auto-commit/push flags
    GIT_ENABLE_AUTOCOMMIT: bool = False
    GIT_REPO_DIR: str = ""
    GIT_REMOTE_NAME: str = "origin"
    GIT_BRANCH: str = "main"
    GIT_USER_NAME: str = "Heimdall Bot"
    GIT_USER_EMAIL: str = "heimdall-bot@valhalla.local"
    GITHUB_TOKEN: str = ""  # optional for private repos

    # --- Embeddings ---
    EMBEDDING_PROVIDER: str = "local"  # local | (future: openai, etc.)
    EMBEDDING_DIM: int = 256
    EMBEDDING_BATCH_SIZE: int = 25

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes")
        return bool(v)

    def get_cors_origins(self) -> List[str]:
        """Parse CORS_ALLOWED_ORIGINS as comma-separated string or return defaults."""
        if self.CORS_ALLOWED_ORIGINS:
            return [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]
        return [
            "https://valhalla.weweb-preview.io",
            "https://editor.weweb.io",
            "https://preview.weweb.io",
            "https://*.weweb.io",
        ]


settings = Settings()
