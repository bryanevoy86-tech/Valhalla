"""
Outbox dispatcher (fail-closed).
This prevents SANDBOX bypass via queued notifications.

If your project already has an outbox dispatcher, keep this file as reference
and apply the same guard_outreach() call at the real dispatch point.
"""

from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session

from app.core.db import get_db  # your shim; adjust if needed
from app.core.engines.dispatch_guard import guard_outreach

# If your Outbox model lives elsewhere, update the import:
# - app.models.notify import Outbox
# - app.models.outbox import Outbox
try:
    from app.models.notify import Outbox  # type: ignore
except Exception:  # pragma: no cover
    Outbox = None  # type: ignore


def dispatch_outbox_once(db: Session = None, limit: int = 50) -> dict:
    """
    One pass dispatch. Safe to call from cron/scheduler.
    Blocks outbound effects if wholesaling is SANDBOX/DORMANT/DISABLED.
    """
    guard_outreach("wholesaling")

    if Outbox is None:
        return {"ok": False, "error": "Outbox model not found", "sent": 0}

    if db is None:
        from app.core.db import SessionLocal
        db = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        sent = 0
        rows = (
            db.query(Outbox)
            .filter(Outbox.status == "queued")  # adjust if your status differs
            .order_by(Outbox.id.asc())
            .limit(limit)
            .all()
        )

        for r in rows:
            # Fail-closed per message as well (double-guard)
            guard_outreach("wholesaling")

            # Your actual dispatch logic likely lives elsewhere.
            # Here we mark as "dispatched" safely to prevent repeat loops.
            # Replace with actual send logic if you have it.
            r.status = "dispatched"
            sent += 1

        db.commit()
        return {"ok": True, "sent": sent}
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e), "sent": 0}
    finally:
        if should_close:
            db.close()
