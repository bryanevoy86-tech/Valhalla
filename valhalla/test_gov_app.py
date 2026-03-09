"""Minimal Valhalla Governance Test App - standalone server"""
import sys
import os
from pathlib import Path

# Determine backend directory
this_file = Path(__file__).resolve()
if this_file.parent.name == 'backend':
    # Already running from backend directory
    backend_dir = str(this_file.parent)
else:
    # Running from repo root, add backend to path
    backend_dir = str(this_file.parent / 'backend')

# Add backend to sys.path
if backend_dir not in sys.path and '.' not in sys.path:
    sys.path.insert(0, backend_dir)

# Change working directory to backend and ensure . is in path
os.chdir(backend_dir)
if '.' not in sys.path:
    sys.path.insert(0, '.')

from fastapi import FastAPI
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Valhalla Governance Test"
    SECRET_KEY: str = "test-secret-key"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

app = FastAPI(title=settings.PROJECT_NAME)

# Import our governance core router
from app.core_gov.telemetry.logger import configure_logging
from app.core_gov.telemetry.exceptions import unhandled_exception_handler
from app.core_gov.core_router import core as core_router

# Configure logging and exception handling
configure_logging()
app.add_exception_handler(Exception, unhandled_exception_handler)

# Include the governance core router
app.include_router(core_router)

# Register all engines at startup
from app.engines.register import register_all_engines
register_all_engines()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="warning")
