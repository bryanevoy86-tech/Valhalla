# app.db package marker
"""
Compatibility shim.

Some routers import get_db from app.db, others from app.core.db.
Canonical location: app.core.db.get_db

This file re-exports get_db so legacy imports do not break.
"""

from app.core.db import get_db  # noqa: F401

__all__ = ["get_db"]