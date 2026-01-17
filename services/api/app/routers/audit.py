from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.audit.schemas import AuditEventCreate, AuditEventResponse
from app.audit.service import log_event, list_events


router = APIRouter(prefix="/audit", tags=["audit"])


@router.post("/", response_model=AuditEventResponse)
def write_audit(event: AuditEventCreate, db: Session = Depends(get_db)):
    return log_event(db, event)


@router.get("/", response_model=List[AuditEventResponse])
def recent_audit(limit: int = 200, db: Session = Depends(get_db)):
    return list_events(db, limit=limit)
