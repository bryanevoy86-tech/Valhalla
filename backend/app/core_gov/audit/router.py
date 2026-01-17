from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from .schemas import AuditEventCreate, AuditListResponse
from . import service

router = APIRouter(prefix="/core/audit", tags=["core-audit"])


@router.post("/event")
def log_event(payload: AuditEventCreate):
    try:
        return service.log(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/events", response_model=AuditListResponse)
def events(
    limit: int = Query(default=100, ge=1, le=500),
    level: Optional[str] = None,
    event_type: Optional[str] = None,
    ref_id: Optional[str] = None,
):
    return {"items": service.list_events(limit=limit, level=level, event_type=event_type, ref_id=ref_id)}
