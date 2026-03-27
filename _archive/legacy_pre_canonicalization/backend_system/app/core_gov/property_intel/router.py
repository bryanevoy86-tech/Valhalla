from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from .schemas import (
    PropertyIntelCreate,
    CompCreate,
    RepairLineCreate,
    PropertyListResponse,
    CompListResponse,
    RepairListResponse,
    IntelSummaryResponse,
)
from . import service

router = APIRouter(prefix="/core/property-intel", tags=["core-property-intel"])


@router.post("/properties")
def create_property(payload: PropertyIntelCreate):
    try:
        return service.create_property(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/properties", response_model=PropertyListResponse)
def list_properties(country: Optional[str] = None):
    return {"items": service.list_properties(country=country)}


@router.post("/comps")
def create_comp(payload: CompCreate):
    try:
        return service.create_comp(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/comps", response_model=CompListResponse)
def list_comps(property_intel_id: Optional[str] = None):
    return {"items": service.list_comps(property_intel_id=property_intel_id)}


@router.post("/repairs")
def create_repair(payload: RepairLineCreate):
    try:
        return service.create_repair(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/repairs", response_model=RepairListResponse)
def list_repairs(property_intel_id: Optional[str] = None):
    return {"items": service.list_repairs(property_intel_id=property_intel_id)}


@router.get("/summary/{property_intel_id}", response_model=IntelSummaryResponse)
def get_summary(property_intel_id: str):
    try:
        return service.get_intel_summary(property_intel_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
