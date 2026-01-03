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


@router.post("/rent_repairs", response_model=RentRepairResponse)
def rent_repairs(payload: RentRepairRequest):
    return service.rent_repairs(payload.model_dump())
