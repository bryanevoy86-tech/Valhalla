"""Record durable policy evidence on the canonical freeze model."""

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.freeze_events import FreezeEvent


FREEZE_EVENT_TYPES = ("freeze", "underwriting_policy_violation", "profit_policy_violation")


def log_freeze_event(
    db: Session,
    *,
    source: str | None = None,
    event_type: str = "freeze",
    severity: str | None = None,
    reason: str | None = None,
    payload: dict[str, Any] | None = None,
    notes: str | None = None,
    resolved: bool = False,
    resolved_by: str | None = None,
    commit: bool = True,
) -> FreezeEvent:
    evidence = payload or {}
    deal_id = evidence.get("backend_deal_id", evidence.get("deal_id"))
    event = FreezeEvent(
        deal_id=str(deal_id) if deal_id is not None else None,
        source=source,
        event_type=event_type,
        severity=severity,
        reason=reason,
        payload=payload,
        notes=notes,
        is_completed=resolved,
        resolved_at=datetime.utcnow() if resolved else None,
        resolved_by=resolved_by if resolved else None,
    )
    db.add(event)
    if commit:
        db.commit()
        db.refresh(event)
    else:
        db.flush()
    return event


def resolve_freeze_event(
    db: Session,
    freeze_event_id: int,
    *,
    resolved_by: str = "system",
    notes: str | None = None,
) -> FreezeEvent | None:
    event = db.get(FreezeEvent, freeze_event_id, with_for_update=True)
    if event is None or event.is_completed:
        return event
    event.is_completed = True
    event.resolved_at = datetime.utcnow()
    event.resolved_by = resolved_by
    if notes:
        event.notes = (event.notes or "") + f"\n[resolved] {notes}"
    db.commit()
    db.refresh(event)
    return event


def get_deal_freezes(db: Session, deal_id: int) -> list[FreezeEvent]:
    return (
        db.query(FreezeEvent)
        .filter(
            FreezeEvent.deal_id == str(deal_id),
            FreezeEvent.event_type.in_(FREEZE_EVENT_TYPES),
        )
        .order_by(FreezeEvent.created_at.desc(), FreezeEvent.id.desc())
        .all()
    )
