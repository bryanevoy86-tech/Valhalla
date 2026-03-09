from __future__ import annotations

from fastapi import APIRouter, Query

from .schemas import SnapshotResponse, SnapshotListResponse
from . import service

router = APIRouter(prefix="/core/analytics", tags=["core-analytics"])


@router.get("/snapshot", response_model=SnapshotResponse)
def snapshot():
    snap = service.snapshot()
    return {"snapshot": snap}


@router.post("/snapshot", response_model=SnapshotResponse)
def snapshot_store():
    snap = service.snapshot_and_store()
    return {"snapshot": snap}


@router.get("/history", response_model=SnapshotListResponse)
def history(limit: int = Query(default=50, ge=1, le=500)):
    return {"items": service.list_history(limit=limit)}
