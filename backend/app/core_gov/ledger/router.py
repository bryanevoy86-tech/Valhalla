from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/ledger", tags=["core-ledger"])

@router.post("")
def create(
    kind: str,
    date: str,
    amount: float,
    description: str = "",
    category: str = "",
    merchant: str = "",
    account_id: str = "",
    obligation_id: str = "",
    receipt_id: str = "",
    tags: List[str] = None,
    meta: Dict[str, Any] = None
):
    try:
        return service.create(kind=kind, date=date, amount=amount, description=description, category=category, merchant=merchant,
                              account_id=account_id, obligation_id=obligation_id, receipt_id=receipt_id, tags=tags, meta=meta or {})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(kind: str = "", category: str = "", account_id: str = "", q: str = "", date_from: str = "", date_to: str = ""):
    return {"items": service.list_items(kind=kind, category=category, account_id=account_id, q=q, date_from=date_from, date_to=date_to)}

@router.get("/summary")
def summary(date_from: str = "", date_to: str = ""):
    return service.summary(date_from=date_from, date_to=date_to)
