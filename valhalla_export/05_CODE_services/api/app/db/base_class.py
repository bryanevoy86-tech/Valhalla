"""
Compatibility shim.

Older models import Base from `app.db.base_class`.
Newer code defines Base in `app.core.db`.

This file keeps old imports working without touching 40+ models.
"""

from app.core.db import Base  # re-export

__all__ = ["Base"]
