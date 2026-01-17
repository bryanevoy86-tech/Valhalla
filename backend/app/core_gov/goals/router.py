from __future__ import annotations
from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/goals", tags=["core-goals"])

@router.post("")
def create(title: str, target_amount: float, due_date: str = "", vault_id: str = "", priority: str = "normal", notes: str = ""):
    try:
        return service.create(title=title, target_amount=target_amount, due_date=due_date, vault_id=vault_id, priority=priority, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "active"):
    return {"items": service.list_items(status=status)}
