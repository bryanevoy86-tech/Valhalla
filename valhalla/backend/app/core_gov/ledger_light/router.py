from __future__ import annotations
from fastapi import APIRouter, HTTPException
from . import service
from .reports import month_summary

router = APIRouter(prefix="/core/ledger", tags=["core-ledger-light"])

@router.post("")
def create(date: str, kind: str, amount: float, description: str = "", category: str = "", account_id: str = ""):
    try:
        return service.create(date_str=date, kind=kind, amount=amount, description=description, category=category, account_id=account_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_tx(kind: str = "", category: str = "", account_id: str = "", limit: int = 500):
    return {"tx": service.list_tx(kind=kind, category=category, account_id=account_id, limit=limit)}

@router.get("/month")
def month(month: str):
    # month = YYYY-MM
    return month_summary(prefix=month)
