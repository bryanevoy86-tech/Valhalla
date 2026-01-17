# services/api/app/services/freeze_events.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.models.freeze_events import FreezeEvent


def log_freeze_event(
    db: Session,
    *,
    source: Optional[str] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    reason: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    notes: Optional[str] = None,
    resolved: bool = False,
    resolved_by: Optional[str] = None,
) -> FreezeEvent:
    """
    Create a freeze event safely. This will **never crash your scheduler**.

    Returns the created FreezeEvent ORM object.
    """

    try:
        event = FreezeEvent(
            source=source,
            event_type=event_type,
            severity=severity,
            reason=reason,
            payload=payload,
            notes=notes,
            resolved_at=datetime.utcnow() if resolved else None,
            resolved_by=resolved_by,
        )

        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    except (ProgrammingError, OperationalError):
        # Database not ready or table missing — DO NOT kill scheduler
        # Instead swallow the error and return a synthetic object.
        db.rollback()
        return FreezeEvent(
            id=-1,  # sentinel id for "not actually saved"
            created_at=datetime.utcnow(),
            source=source,
            event_type=event_type,
            severity=severity,
            reason=reason,
            payload=payload,
            notes="Event not saved due to DB issue (dev mode or migration missing).",
        )


def resolve_freeze_event(
    db: Session,
    freeze_event_id: int,
    *,
    resolved_by: str = "system",
    notes: Optional[str] = None,
) -> Optional[FreezeEvent]:
    """
    Mark a freeze event as resolved.
    Returns the updated object or None if not found.
    """

    try:
        event = db.query(FreezeEvent).filter(FreezeEvent.id == freeze_event_id).first()
    except (ProgrammingError, OperationalError):
        db.rollback()
        return None

    if not event:
        return None

    event.resolved_at = datetime.utcnow()
    event.resolved_by = resolved_by
    if notes:
        event.notes = (event.notes or "") + f"\n[resolved] {notes}"

    db.add(event)
    db.commit()
    db.refresh(event)
    return event
