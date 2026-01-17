"""PACK-CORE-PRELAUNCH-01: Unified Log - Service"""

from typing import List, Optional

from sqlalchemy.orm import Session

from . import models, schemas


def log_event(db: Session, data: schemas.SystemEventCreate) -> models.SystemEvent:
    event = models.SystemEvent(**data.dict())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events(
    db: Session,
    event_type: Optional[models.EventType] = None,
    source: Optional[str] = None,
    limit: int = 200,
) -> List[models.SystemEvent]:
    q = db.query(models.SystemEvent)
    if event_type:
        q = q.filter(models.SystemEvent.event_type == event_type)
    if source:
        q = q.filter(models.SystemEvent.source == source)
    return q.order_by(models.SystemEvent.timestamp.desc()).limit(limit).all()
