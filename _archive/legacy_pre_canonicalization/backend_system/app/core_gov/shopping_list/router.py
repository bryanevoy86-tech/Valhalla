from __future__ import annotations
from fastapi import APIRouter, HTTPException
from . import service
from .ops import to_followups

router = APIRouter(prefix="/core/shopping", tags=["core-shopping"])

@router.post("")
def add(item: str, category: str = "household", priority: str = "normal", qty: float = 1.0, notes: str = ""):
    try:
        return service.add(item=item, category=category, priority=priority, qty=qty, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "open", category: str = ""):
    return {"items": service.list_items(status=status, category=category)}

@router.post("/{item_id}/mark")
def mark(item_id: str, status: str):
    try:
        return service.mark(item_id=item_id, status=status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")

@router.post("/followups")
def create_followups(status: str = "open"):
    return to_followups(status=status)
