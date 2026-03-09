import os
import logging

log = logging.getLogger("valhalla.startup")


def should_auto_create_schema() -> bool:
    """Check if automatic schema creation on startup is enabled.
    
    Default is OFF in Render/Prod since Alembic migrations handle schema.
    Only turn on if you explicitly need it for local development.
    """
    return os.getenv("AUTO_CREATE_SCHEMA", "0") == "1"
