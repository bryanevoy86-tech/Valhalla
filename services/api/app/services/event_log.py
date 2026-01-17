"""
PACK AH: Event Log / Timeline Engine Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.event_log import EventLog
from app.schemas.event_log import EventLogCreate


def record_event(db: Session, payload: EventLogCreate) -> EventLog:
    """Record a new event to the timeline"""
    obj = EventLog(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_events_for_entity(
    db: Session,
    entity_type: str,
    entity_id: Optional[str] = None,
    limit: int = 100,
) -> List[EventLog]:
    """List events for a specific entity, optionally filtered by entity_id"""
    q = db.query(EventLog).filter(EventLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(EventLog.entity_id == entity_id)
    return q.order_by(EventLog.created_at.desc()).limit(limit).all()


def list_recent_events(db: Session, limit: int = 100) -> List[EventLog]:
    """List recent events across all entities"""
    return (
        db.query(EventLog)
        .order_by(EventLog.created_at.desc())
        .limit(limit)
        .all()
    )
