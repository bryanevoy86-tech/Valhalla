from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/shopping_list", tags=["core-shopping-list"])

@router.post("")
def add(item: str, qty: float = 1.0, unit: str = "each", priority: str = "normal", category: str = "grocery", notes: str = ""):
    try:
        return service.add(item=item, qty=qty, unit=unit, priority=priority, category=category, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "open", category: str = "", q: str = ""):
    return {"items": service.list_items(status=status, category=category, q=q)}

@router.post("/{item_id}/status")
def set_status(item_id: str, status: str):
    try:
        return service.mark(item_id=item_id, status=status)
    except KeyError:
        raise HTTPException(status_code=404, detail="item not found")
