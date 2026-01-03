"""P-MONTHCLOSE-1: Month close router."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from . import service

router = APIRouter(prefix="/core/month_close", tags=["month_close"])

class CloseRequest(BaseModel):
    month: str
    notes: str = ""

class CloseResponse(BaseModel):
    id: str
    month: str
    snapshot: dict
    created_at: str

@router.post("")
def create_close(req: CloseRequest) -> CloseResponse:
    """Create a month close snapshot."""
    item = service.close(req.month, req.notes)
    return CloseResponse(**item)

@router.get("")
def list_closes() -> list[CloseResponse]:
    """List all month close snapshots."""
    items = service.list_snapshots()
    return [CloseResponse(**item) for item in items]
