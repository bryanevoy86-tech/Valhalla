from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException

from .schemas import ScheduleCreate, ScheduleListResponse
from . import service

router = APIRouter(prefix="/core/schedule", tags=["core-schedule"])


@router.post("")
def create(payload: ScheduleCreate):
    try:
        return service.create(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ScheduleListResponse)
def list_all(status: Optional[str] = None, priority: Optional[str] = None, due_date: Optional[str] = None):
    return {"items": service.list_all(status=status, priority=priority, due_date=due_date)}


@router.patch("/{sid}")
def patch(sid: str, patch: Dict[str, Any]):
    try:
        return service.patch(sid, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="schedule item not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
