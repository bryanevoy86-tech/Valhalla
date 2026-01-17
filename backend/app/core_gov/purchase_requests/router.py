from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/purchase_requests", tags=["core-purchase-requests"])

@router.post("")
def create(title: str, category: str = "general", priority: str = "normal", desired_by: str = "", est_cost: float = 0.0, notes: str = ""):
    try:
        return service.create(title=title, category=category, priority=priority, desired_by=desired_by, est_cost=est_cost, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = ""):
    return {"items": service.list_items(status=status)}

@router.post("/{req_id}/approve")
def approve(req_id: str, auto_create_shopping: bool = True, auto_create_reminder: bool = True):
    try:
        return service.approve(req_id=req_id, auto_create_shopping=auto_create_shopping, auto_create_reminder=auto_create_reminder)
    except KeyError:
        raise HTTPException(status_code=404, detail="request not found")
