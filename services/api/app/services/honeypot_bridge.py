"""
PACK TS: Honeypot Bridge Services
Business logic for honeypot instance and event management.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
import secrets

from app.models.honeypot_bridge import HoneypotInstance, HoneypotEvent


async def create_instance(
    db: Session,
    name: str,
    honeypot_type: str,
    location: str = None,
    metadata: dict = None
) -> HoneypotInstance:
    """Create a new honeypot instance with API key."""
    api_key = secrets.token_urlsafe(32)
    instance = HoneypotInstance(
        name=name,
        api_key=api_key,
        honeypot_type=honeypot_type,
        location=location,
        metadata=metadata,
        active=True
    )
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


async def get_instance_by_api_key(db: Session, api_key: str) -> HoneypotInstance:
    """Get honeypot instance by API key."""
    return db.query(HoneypotInstance).filter(
        HoneypotInstance.api_key == api_key,
        HoneypotInstance.active == True
    ).first()


async def get_instance(db: Session, instance_id: int) -> HoneypotInstance:
    """Get honeypot instance by ID."""
    return db.query(HoneypotInstance).filter(
        HoneypotInstance.id == instance_id
    ).first()


async def list_instances(db: Session, active_only: bool = True):
    """List honeypot instances."""
    query = db.query(HoneypotInstance)
    
    if active_only:
        query = query.filter(HoneypotInstance.active == True)
    
    items = query.order_by(desc(HoneypotInstance.created_at)).all()
    total = db.query(HoneypotInstance).count()
    active = db.query(HoneypotInstance).filter(HoneypotInstance.active == True).count()
    
    return {
        "total": total,
        "active_instances": active,
        "items": items
    }


async def record_event(
    db: Session,
    honeypot_id: int,
    source_ip: str,
    event_type: str,
    payload: dict = None,
    detected_threat: str = None
) -> HoneypotEvent:
    """Record a honeypot event."""
    event = HoneypotEvent(
        honeypot_id=honeypot_id,
        source_ip=source_ip,
        event_type=event_type,
        payload=payload,
        detected_threat=detected_threat,
        processed=False
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


async def list_events(
    db: Session,
    honeypot_id: int = None,
    unprocessed_only: bool = False,
    limit: int = 100
):
    """List honeypot events."""
    query = db.query(HoneypotEvent)
    
    if honeypot_id:
        query = query.filter(HoneypotEvent.honeypot_id == honeypot_id)
    
    if unprocessed_only:
        query = query.filter(HoneypotEvent.processed == False)
    
    items = query.order_by(desc(HoneypotEvent.created_at)).limit(limit).all()
    total = db.query(HoneypotEvent).count()
    unprocessed = db.query(HoneypotEvent).filter(
        HoneypotEvent.processed == False
    ).count()
    
    return {
        "total": total,
        "unprocessed": unprocessed,
        "items": items
    }


async def mark_event_processed(db: Session, event_id: int) -> HoneypotEvent:
    """Mark event as processed."""
    event = db.query(HoneypotEvent).filter(HoneypotEvent.id == event_id).first()
    if not event:
        return None
    
    event.processed = True
    db.commit()
    db.refresh(event)
    return event


async def deactivate_instance(db: Session, instance_id: int) -> HoneypotInstance:
    """Deactivate a honeypot instance."""
    instance = await get_instance(db, instance_id)
    if not instance:
        return None
    
    instance.active = False
    db.commit()
    db.refresh(instance)
    return instance
