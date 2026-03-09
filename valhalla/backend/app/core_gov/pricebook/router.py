from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/pricebook", tags=["core-pricebook"])

@router.post("")
def create(item_name: str, typical_unit_price: float, unit: str = "each", preferred_store: str = "", status: str = "active", notes: str = ""):
    try:
        return service.create(item_name=item_name, typical_unit_price=typical_unit_price, unit=unit, preferred_store=preferred_store, status=status, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = ""):
    return {"items": service.list_items(status=status)}

@router.get("/find")
def find(item_name: str):
    x = service.find(item_name=item_name)
    return {"item": x}
