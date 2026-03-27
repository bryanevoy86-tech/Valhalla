from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/big_purchases", tags=["core-big-purchases"])

@router.post("")
def create(title: str, target_amount: float, target_date: str = "", vault_id: str = "", vault_name: str = "", priority: str = "normal", notes: str = ""):
    try:
        return service.create(title=title, target_amount=target_amount, target_date=target_date, vault_id=vault_id, vault_name=vault_name, priority=priority, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "active", q: str = ""):
    return {"items": service.list_items(status=status, q=q)}

@router.get("/{purchase_id}/funding_status")
def funding_status(purchase_id: str):
    try:
        return service.funding_status(purchase_id=purchase_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="purchase not found")
