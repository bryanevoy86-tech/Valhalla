from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/autopay_setups", tags=["core-autopay-setups"])

@router.post("")
def create(obligation_id: str, guide_id: str = "", status: str = "pending", notes: str = ""):
    try:
        return service.create(obligation_id=obligation_id, guide_id=guide_id, status=status, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "", obligation_id: str = ""):
    return {"items": service.list_items(status=status, obligation_id=obligation_id)}

@router.post("/{setup_id}/status")
def set_status(setup_id: str, status: str):
    try:
        return service.set_status(setup_id=setup_id, status=status)
    except KeyError:
        raise HTTPException(status_code=404, detail="setup not found")
