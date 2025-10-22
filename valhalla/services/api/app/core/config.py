from pydantic_settings import BaseSettings, SettingsConfigDictfrom pydantic_settings import BaseSettings

from pydantic import field_validatorfrom typing import List

from typing import Listimport os

import os

class Settings(BaseSettings):

class Settings(BaseSettings):    ENV: str = os.getenv("ENV", "prod")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    

    ENV: str = "prod"    # Render injects PORT; we dont need it here but leaving for ref

    DEBUG: bool = False    PORT: int = int(os.getenv("PORT", "8000"))

    PORT: int = 8000

        # Database (Render Postgres or your own)

    # Database (Render Postgres or your own)    DATABASE_URL: str = os.getenv(

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/valhalla"        "DATABASE_URL",

        "postgresql+psycopg://postgres:postgres@localhost:5432/valhalla"

    # CORS - will be parsed from comma-separated string    )

    CORS_ALLOWED_ORIGINS: str = ""

    # CORS

    # Heimdall Builder flags    CORS_ALLOWED_ORIGINS: List[str] = [

    HEIMDALL_BUILDER: str = "off"        o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()

    BUILDER_SAFE_MODE: str = "on"    ] or [

    AUTO_DEPLOY: str = "off"        "https://valhalla.weweb-preview.io",

    ALLOW_DESTRUCTIVE: str = "off"        "https://editor.weweb.io",

    HEIMDALL_BUILDER_API_KEY: str = ""        "https://preview.weweb.io",

            "https://*.weweb.io",

    # Builder settings    ]

    BUILDER_ALLOWED_DIRS: List[str] = [

        "services/api/app/routers",    # Heimdall Builder flags

        "services/api/app/models",    HEIMDALL_BUILDER: str = os.getenv("HEIMDALL_BUILDER", "off")

        "services/api/app/schemas",    BUILDER_SAFE_MODE: str = os.getenv("BUILDER_SAFE_MODE", "on")

        "services/api/app/core",    AUTO_DEPLOY: str = os.getenv("AUTO_DEPLOY", "off")

        "services/api/alembic/versions",    ALLOW_DESTRUCTIVE: str = os.getenv("ALLOW_DESTRUCTIVE", "off")

        "services/worker",

        ".github/workflows",    HEIMDALL_BUILDER_API_KEY: str | None = os.getenv("HEIMDALL_BUILDER_API_KEY")

    ]

    BUILDER_MAX_FILE_BYTES: int = 200000  # 200KBsettings = Settings()


    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes")
        return bool(v)

    def get_cors_origins(self) -> List[str]:
        """Parse CORS_ALLOWED_ORIGINS as comma-separated string"""
        if self.CORS_ALLOWED_ORIGINS:
            return [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]
        return [
            "https://valhalla.weweb-preview.io",
            "https://editor.weweb.io",
            "https://preview.weweb.io",
            "https://*.weweb.io",
        ]

settings = Settings()
