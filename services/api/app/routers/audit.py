from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.audit.schemas import AuditEventCreate, AuditEventResponse
from app.audit.service import log_event, list_events


router = APIRouter(prefix="/audit", tags=["audit"])


@router.post("/", response_model=AuditEventResponse)
def write_audit(event: AuditEventCreate, db: Session = Depends(get_db)):
    """Write an audit event to persistent storage."""
    return log_event(db, event)


@router.get("/", response_model=List[AuditEventResponse])
def recent_audit(limit: int = 200, db: Session = Depends(get_db)):
    """Get recent audit events (system-wide, up to limit)."""
    return list_events(db, limit=limit)


@router.get("/deals/{deal_id}", response_model=List[AuditEventResponse])
def get_deal_audit_trail(deal_id: int, db: Session = Depends(get_db)):
    """
    Get complete audit trail for a specific deal.
    
    Returns all audit events related to this deal_id, ordered by creation date (newest first).
    """
    from app.audit.models import AuditEvent
    
    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.entity_type == "deal", AuditEvent.entity_id == deal_id)
        .order_by(AuditEvent.created_at.desc())
        .all()
    )
    
    return events

