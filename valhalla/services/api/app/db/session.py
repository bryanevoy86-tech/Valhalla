"""Database session factory for compatibility and convenience."""
from sqlalchemy.orm import Session
from app.core.db import SessionLocal, get_db

__all__ = ["SessionLocal", "get_db", "Session"]
