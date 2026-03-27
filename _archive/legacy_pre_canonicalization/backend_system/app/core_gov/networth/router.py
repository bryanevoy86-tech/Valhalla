from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from .schemas import LineItemCreate, LineItemListResponse
from . import service

router = APIRouter(prefix="/core/networth", tags=["core-networth"])


@router.post("/items")
def create_item(payload: LineItemCreate):
    try:
        return service.create_item(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/items", response_model=LineItemListResponse)
def list_items(status: str = ""):
    return {"items": service.list_items(status=status)}


@router.patch("/items/{item_id}")
def patch(item_id: str, patch: Dict[str, Any]):
    try:
        return service.patch(item_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="item not found")


@router.post("/snapshot")
def snapshot(note: str = ""):
    return service.snapshot(note=note)


@router.get("/snapshots")
def snapshots(limit: int = 25):
    return {"items": service.list_snapshots(limit=limit)}
