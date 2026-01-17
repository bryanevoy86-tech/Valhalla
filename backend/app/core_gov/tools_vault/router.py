from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/tools_vault", tags=["core-tools-vault"])

@router.post("")
def create(name: str, est_value: float = 0.0, status: str = "listed", notes: str = ""):
    try:
        return service.create(name=name, est_value=est_value, status=status, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = ""):
    return {"items": service.list_items(status=status)}

@router.post("/{item_id}/sold")
def sold(item_id: str, sold_price: float, sold_date: str, deposit_to_vault_id: str = "", note: str = ""):
    try:
        return service.mark_sold(item_id=item_id, sold_price=sold_price, sold_date=sold_date, deposit_to_vault_id=deposit_to_vault_id, note=note)
    except KeyError:
        raise HTTPException(status_code=404, detail="item not found")
