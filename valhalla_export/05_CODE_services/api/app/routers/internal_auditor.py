# services/api/app/routers/internal_auditor.py

from __future__ import annotations

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.audit_event import AuditEventOut
from app.services.internal_auditor import (
    scan_deal,
    list_open_events,
    list_events_for_deal,
    resolve_audit_event,
    get_audit_summary,
)

router = APIRouter(
    prefix="/audit",
    tags=["Audit", "Internal"]
)


@router.post("/scan/deal/{deal_id}")
def audit_deal(deal_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Run audit rules on a single deal and emit AuditEvents as needed.
    
    Checks for:
    - Missing signed contracts (critical)
    - Unacknowledged documents (warning)
    - Open professional tasks (warning)
    """
    return scan_deal(db, deal_id)


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get summary of open audit events by severity."""
    return get_audit_summary(db)


@router.get("/events/open", response_model=List[AuditEventOut])
def get_open_events(db: Session = Depends(get_db)):
    """Get all unresolved audit events across the system."""
    return list_open_events(db)


@router.get("/events/deal/{deal_id}", response_model=List[AuditEventOut])
def get_deal_events(deal_id: int, db: Session = Depends(get_db)):
    """Get all audit events for a specific deal."""
    return list_events_for_deal(db, deal_id)


@router.post("/events/{event_id}/resolve", response_model=AuditEventOut)
def resolve_event(event_id: int, db: Session = Depends(get_db)):
    """Mark an audit event as resolved."""
    evt = resolve_audit_event(db, event_id)
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    return evt
