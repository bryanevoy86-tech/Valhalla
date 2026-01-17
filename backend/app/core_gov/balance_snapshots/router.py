from __future__ import annotations
from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/balances", tags=["core-balance-snapshots"])

@router.post("")
def create(date: str, account_id: str, balance: float, currency: str = "", notes: str = ""):
    try:
        return service.create(date=date, account_id=account_id, balance=balance, currency=currency, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_recent(account_id: str = "", limit: int = 50):
    return {"items": service.list_recent(account_id=account_id, limit=limit)}

@router.get("/runway")
def runway(account_id: str):
    from .runway import estimate
    return estimate(account_id=account_id)
