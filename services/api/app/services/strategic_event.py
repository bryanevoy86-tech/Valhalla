"""
PACK L0-09: Strategic Event Service
Records strategic events from various modules.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.strategic_event import StrategicEvent
from app.schemas.strategic_event import StrategicEventCreate


def record_event(
    db: Session,
    tenant_id: str,
    source: str,
    category: str,
    label: str,
    payload: Optional[dict] = None,
    importance_score: float = 0.5,
) -> StrategicEvent:
    """Record a strategic event."""
    event = StrategicEvent(
        tenant_id=tenant_id,
        source=source,
        category=category,
        label=label,
        payload=payload or {},
        importance_score=min(1.0, max(0.0, importance_score)),
        timestamp=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events(
    db: Session,
    tenant_id: str,
    source: Optional[str] = None,
    category: Optional[str] = None,
    min_importance: float = 0.0,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[List[StrategicEvent], int]:
    """List strategic events with filtering."""
    query = db.query(StrategicEvent).filter(StrategicEvent.tenant_id == tenant_id)
    
    if source:
        query = query.filter(StrategicEvent.source == source)
    
    if category:
        query = query.filter(StrategicEvent.category == category)
    
    if min_importance > 0:
        query = query.filter(StrategicEvent.importance_score >= min_importance)
    
    if date_from:
        query = query.filter(StrategicEvent.timestamp >= date_from)
    
    if date_to:
        query = query.filter(StrategicEvent.timestamp <= date_to)
    
    total = query.count()
    items = query.order_by(StrategicEvent.timestamp.desc()).offset(skip).limit(limit).all()
    return items, total


def get_event(db: Session, event_id: int) -> Optional[StrategicEvent]:
    """Get a specific strategic event."""
    return db.query(StrategicEvent).filter(StrategicEvent.id == event_id).first()


def list_events_by_date_range(
    db: Session,
    tenant_id: str,
    days: int = 30,
) -> List[StrategicEvent]:
    """List recent strategic events (last N days)."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(StrategicEvent)
        .filter(
            StrategicEvent.tenant_id == tenant_id,
            StrategicEvent.timestamp >= cutoff
        )
        .order_by(StrategicEvent.timestamp.desc())
        .all()
    )


def delete_event(db: Session, event_id: int) -> bool:
    """Delete a strategic event."""
    event = db.query(StrategicEvent).filter(StrategicEvent.id == event_id).first()
    if not event:
        return False
    
    db.delete(event)
    db.commit()
    return True
