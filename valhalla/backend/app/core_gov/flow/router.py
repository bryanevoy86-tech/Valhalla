from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException

from .schemas import SupplyItemCreate, SupplyListResponse, InventoryUpdate, ShoppingAddRequest, ShoppingListResponse
from . import service

router = APIRouter(prefix="/core/flow", tags=["core-flow"])


@router.post("/items")
def create_item(payload: SupplyItemCreate):
    try:
        return service.create_item(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/items", response_model=SupplyListResponse)
def list_items(status: Optional[str] = None, item_type: Optional[str] = None, tag: Optional[str] = None):
    return {"items": service.list_items(status=status, item_type=item_type, tag=tag)}


@router.patch("/items/{item_id}")
def patch_item(item_id: str, patch: Dict[str, Any]):
    try:
        return service.patch_item(item_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="item not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/inventory")
def upsert_inventory(payload: InventoryUpdate):
    try:
        return service.upsert_inventory(payload.model_dump())
    except KeyError:
        raise HTTPException(status_code=404, detail="item not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/inventory/{item_id}")
def get_inventory(item_id: str):
    inv = service.get_inventory(item_id)
    if not inv:
        raise HTTPException(status_code=404, detail="inventory not found")
    return inv


@router.post("/shopping/add")
def shopping_add(payload: ShoppingAddRequest):
    try:
        return service.add_to_shopping(
            item_id=payload.item_id,
            qty=float(payload.qty or 1.0),
            urgency=payload.urgency,
            note=payload.note or "",
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="item not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/shopping", response_model=ShoppingListResponse)
def shopping_list(status: Optional[str] = None, urgency: Optional[str] = None):
    return {"items": service.list_shopping(status=status, urgency=urgency)}


@router.post("/shopping/{shopping_id}/status")
def shopping_mark(shopping_id: str, status: str):
    try:
        return service.mark_shopping(shopping_id, status=status)
    except KeyError:
        raise HTTPException(status_code=404, detail="shopping item not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
