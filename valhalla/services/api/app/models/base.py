"""
Base model class for SQLAlchemy models.
Re-exports the Base from app.core.db for convenience.
"""
from app.core.db import Base

__all__ = ["Base"]
