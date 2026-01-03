from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException

from .schemas import ItemCreate, ItemListResponse, AdjustRequest
from . import service, reorder

router = APIRouter(prefix="/core/inventory", tags=["core-inventory"])


@router.post("")
def create(payload: ItemCreate):
    try:
        return service.create_item(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ItemListResponse)
def list_items(location: Optional[str] = None, tag: Optional[str] = None, priority: Optional[str] = None):
    return {"items": service.list_items(location=location, tag=tag, priority=priority)}


@router.get("/{item_id}")
def get_one(item_id: str):
    x = service.get_item(item_id)
    if not x:
        raise HTTPException(status_code=404, detail="item not found")
    return x


@router.patch("/{item_id}")
def patch(item_id: str, patch: Dict[str, Any]):
    try:
        return service.patch_item(item_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="item not found")


@router.post("/{item_id}/adjust")
def adjust(item_id: str, payload: AdjustRequest):
    try:
        return service.adjust_stock(item_id, delta=payload.delta, reason=payload.reason, meta=payload.meta)
    except KeyError:
        raise HTTPException(status_code=404, detail="item not found")


@router.get("/reorders/suggest")
def suggest(location: Optional[str] = None, priority: Optional[str] = None, tag: Optional[str] = None, max_items: int = 25):
    return reorder.suggest_reorders(location=location or "", priority=priority or "", tag=tag or "", max_items=max_items)
