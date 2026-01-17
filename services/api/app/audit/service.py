from sqlalchemy.orm import Session
from app.audit.models import AuditEvent
from app.audit.schemas import AuditEventCreate


def log_event(db: Session, payload: AuditEventCreate) -> AuditEvent:
    event = AuditEvent(**payload.dict())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events(db: Session, limit: int = 200):
    return db.query(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit).all()
