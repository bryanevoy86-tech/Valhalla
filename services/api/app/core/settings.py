"""
Settings configuration for the API.
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Default to a file-based SQLite database for better testing and persistence
    # Use in-memory for explicit testing with "memory:" string
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./heimdall.db")
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
