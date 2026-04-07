"""
Compatibility module for database base class.

Older code imports Base from app.db.base, while newer code uses app.core.db.
This file ensures both paths work.
"""

from app.core.db import Base, get_db

__all__ = ["Base", "get_db"]
