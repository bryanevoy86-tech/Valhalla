from sqlalchemy.orm import Session
from app.audit.models import AuditEvent
from app.audit.schemas import AuditEventCreate


def log_event(db: Session, payload: AuditEventCreate) -> AuditEvent:
    """Log an audit event to the database.
    
    Extracts only the fields that map to DB columns.
    Extra fields like actor, target, result are ignored (they're in meta for reference).
    """
    # Only pass fields that exist in the AuditEvent ORM model
    event_data = {
        "action": payload.action,
        "entity_type": payload.entity_type,
        "entity_id": payload.entity_id,
        "previous_value": payload.previous_value,
        "new_value": payload.new_value,
        "user_id": payload.user_id or "system",
        "notes": payload.notes,
    }
    
    event = AuditEvent(**event_data)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events(db: Session, limit: int = 200):
    return db.query(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit).all()
