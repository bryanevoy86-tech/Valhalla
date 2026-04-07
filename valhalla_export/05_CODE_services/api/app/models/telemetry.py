"""
Telemetry model shim.

We keep IntegrityEvent imported from app.integrity.models so that
existing imports like:

	from app.models.telemetry import IntegrityEvent

continue to work, but the actual SQLAlchemy model is defined only once
in app.integrity.models.

This avoids duplicate table definitions and metadata conflicts.
"""

from app.integrity.models import IntegrityEvent

__all__ = ["IntegrityEvent"]

