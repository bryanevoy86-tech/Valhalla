from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException

from .schemas import (
    PropertyCreate,
    PropertyListResponse,
    NeighborhoodRatingRequest,
    NeighborhoodRatingResponse,
    CompsRequest,
    CompsResponse,
    RentRepairRequest,
    RentRepairResponse,
)
from . import service
from .comps import add_comp, comps_summary
from .repairs import add_repair
from .rent import set_rent
from .neighborhood import set_rating
from .arv import set_arv

router = APIRouter(prefix="/core/property", tags=["core-property"])


@router.post("")
def create_property(payload: PropertyCreate):
    try:
        return service.create_property(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=PropertyListResponse)
def list_properties(
    country: Optional[str] = None,
    region: Optional[str] = None,
    deal_id: Optional[str] = None,
    tag: Optional[str] = None,
):
    return {"items": service.list_properties(country=country, region=region, deal_id=deal_id, tag=tag)}


@router.get("/{property_id}")
def get_property(property_id: str):
    p = service.get_property(property_id)
    if not p:
        raise HTTPException(status_code=404, detail="property not found")
    return p


@router.post("/neighborhood_rating", response_model=NeighborhoodRatingResponse)
def neighborhood_rating(payload: NeighborhoodRatingRequest):
    return service.neighborhood_rating(payload.model_dump())


@router.post("/comps", response_model=CompsResponse)
def comps(payload: CompsRequest):
    return service.comps(payload.model_dump())


@router.post("/{prop_id}/comps")
def add_comp_ep(prop_id: str, address: str, sold_price: float, sold_date: str = "", sqft: int = 0, notes: str = ""):
    try:
        return add_comp(prop_id=prop_id, address=address, sold_price=sold_price, sold_date=sold_date, sqft=sqft, notes=notes)
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")

@router.get("/{prop_id}/comps/summary")
def comps_sum(prop_id: str):
    try:
        return comps_summary(prop_id=prop_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")

@router.post("/{prop_id}/repairs")
def add_repair_ep(prop_id: str, item: str, cost: float, notes: str = ""):
    try:
        return add_repair(prop_id=prop_id, item=item, cost=cost, notes=notes)
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")

@router.post("/{prop_id}/rent")
def set_rent_ep(prop_id: str, projected_rent: float, notes: str = ""):
    try:
        return set_rent(prop_id=prop_id, projected_rent=projected_rent, notes=notes)
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")

@router.post("/{prop_id}/neighborhood")
def neighborhood_ep(prop_id: str, score: int, notes: str = ""):
    try:
        return set_rating(prop_id=prop_id, score=score, notes=notes)
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")

@router.post("/{prop_id}/arv")
def set_arv_ep(prop_id: str, arv: float, notes: str = ""):
    try:
        return set_arv(prop_id=prop_id, arv=arv, notes=notes)
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")

@router.post("/rent_repairs", response_model=RentRepairResponse)
def rent_repairs(payload: RentRepairRequest):
    return service.rent_repairs(payload.model_dump())
