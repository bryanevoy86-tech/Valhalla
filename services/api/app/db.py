"""
Compatibility shim.

Some packs import `app.db` from older structure.
We now keep DB plumbing in `app.core.db`, but provide this module so old packs work.
"""

from app.core.db import engine, SessionLocal, get_db_session  # noqa: F401

__all__ = ["engine", "SessionLocal", "get_db_session"]
