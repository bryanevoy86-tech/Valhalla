from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/house_inventory", tags=["core-house-inventory"])

@router.post("")
def upsert(name: str, location: str = "pantry", qty: float = 0.0, min_qty: float = 0.0, unit: str = "each", priority: str = "normal", category: str = "grocery", notes: str = ""):
    try:
        return service.upsert(name=name, location=location, qty=qty, min_qty=min_qty, unit=unit, priority=priority, category=category, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(location: str = "", category: str = "", low_only: bool = False, q: str = ""):
    return {"items": service.list_items(location=location, category=category, low_only=low_only, q=q)}

@router.get("/low_stock")
def low_stock():
    return {"items": service.low_stock()}
