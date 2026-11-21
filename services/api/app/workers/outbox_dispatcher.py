"""Fail-closed reference outbox dispatcher.

This module intentionally does not send messages. It must never mark a
notification delivered without a provider response and persisted receipt.
The actual provider-backed dispatcher, if installed, is a separate pathway.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.engines.dispatch_guard import guard_outreach

try:
    from app.models.notify import Outbox
except ImportError:  # optional model not installed
    Outbox = None


def dispatch_outbox_once(db: Session | None = None, limit: int = 50) -> dict:
    """Inspect pending messages without modifying or pretending to send them."""
    guard_outreach("wholesaling")

    if Outbox is None:
        return {"ok": False, "error": "OUTBOX_MODEL_MISSING", "sent": 0}

    should_close = db is None
    if db is None:
        from app.core.db import SessionLocal

        db = SessionLocal()

    try:
        pending = (
            db.query(Outbox)
            .filter(Outbox.status == "queued")
            .order_by(Outbox.id.asc())
            .limit(limit)
            .all()
        )
        if pending:
            return {
                "ok": False,
                "error": "OUTBOX_TRANSPORT_NOT_CONFIGURED",
                "sent": 0,
                "queued": len(pending),
            }
        return {"ok": True, "sent": 0, "queued": 0}
    except Exception as exc:
        db.rollback()
        return {"ok": False, "error": str(exc), "sent": 0}
    finally:
        if should_close:
            db.close()
