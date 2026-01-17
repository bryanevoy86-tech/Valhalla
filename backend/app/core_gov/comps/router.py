from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException

from . import service

router = APIRouter(prefix="/core/comps", tags=["core-comps"])

@router.post("/")
def create_comp(property_id: str, sold_price: float, sold_date: str, address: str, bed: Optional[int] = None, bath: Optional[float] = None, sqft: Optional[int] = None, distance_km: Optional[float] = None, notes: str = ""):
    try:
        return service.create_comp(property_id=property_id, sold_price=sold_price, sold_date=sold_date, address=address, bed=bed, bath=bath, sqft=sqft, distance_km=distance_km, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def list_comps(property_id: str, limit: int = 200):
    return {"items": service.list_comps_for_property(property_id, limit=limit)}

@router.get("/quick_arv")
def get_quick_arv(property_id: str):
    return service.quick_arv(property_id)
