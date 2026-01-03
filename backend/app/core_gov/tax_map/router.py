"""P-TAXMAP-1: Tax bucket mapping router."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from . import store

router = APIRouter(prefix="/core/tax", tags=["tax"])

class MapRequest(BaseModel):
    category: str
    bucket: str

class MapResponse(BaseModel):
    map: dict[str, str]

@router.get("/map")
def get_map() -> MapResponse:
    """Get current category → bucket mapping."""
    m = store.get_map()
    return MapResponse(map=m)

@router.post("/map")
def save_map(req: MapRequest) -> MapResponse:
    """Update or add a category → bucket mapping."""
    m = store.get_map()
    m[req.category] = req.bucket
    store.save_map(m)
    return MapResponse(map=m)
