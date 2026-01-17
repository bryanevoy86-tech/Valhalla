from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/bank_accounts", tags=["core-bank-accounts"])

@router.post("")
def create(name: str, bank: str, account_type: str = "chequing", country: str = "CA", currency: str = "CAD", last4: str = "", notes: str = ""):
    try:
        return service.create(name=name, bank=bank, account_type=account_type, country=country, currency=currency, last4=last4, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "", q: str = ""):
    return {"items": service.list_items(status=status, q=q)}
