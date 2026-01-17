from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException

from .schemas import ShoppingItemCreate, ShoppingListResponse
from . import service
from . import autofill

router = APIRouter(prefix="/core/shopping", tags=["core-shopping"])


@router.post("")
def create(payload: ShoppingItemCreate):
    try:
        return service.create_item(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ShoppingListResponse)
def list_items(status: str = "", category: str = "", priority: str = "", tag: str = ""):
    return {"items": service.list_items(status=status, category=category, priority=priority, tag=tag)}


@router.get("/{item_id}")
def get_one(item_id: str):
    x = service.get_item(item_id)
    if not x:
        raise HTTPException(status_code=404, detail="shopping item not found")
    return x


@router.patch("/{item_id}")
def patch(item_id: str, patch: Dict[str, Any]):
    try:
        return service.patch_item(item_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="shopping item not found")


@router.post("/{item_id}/mark_purchased")
def mark_purchased(item_id: str, paid_unit_cost: float = 0.0):
    try:
        return service.mark_purchased(item_id, paid_unit_cost=paid_unit_cost)
    except KeyError:
        raise HTTPException(status_code=404, detail="shopping item not found")


@router.post("/autofill_from_inventory")
def autofill_from_inventory(max_create: int = 25):
    return autofill.create_from_inventory(max_create=max_create)

@router.post("/quick_add")
def quick_add(name: str, est_total: float = 0.0, category: str = "household", notes: str = ""):
    # est_total becomes est_unit_cost with qty=1 for simplicity
    try:
        return service.create_item({"name": name, "qty": 1.0, "unit": "each", "category": category, "est_unit_cost": float(est_total or 0.0), "notes": notes})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/request_approvals")
def request_approvals(threshold: float = 200.0):
    from .approvals import request_approvals as req_approvals
    return req_approvals(threshold=threshold)

@router.post("/generate_from_needs")
def generate_from_needs(within_days: int = 30, limit: int = 50):
    from .from_schedule_needs import generate
    return generate(within_days=within_days, limit=limit)
