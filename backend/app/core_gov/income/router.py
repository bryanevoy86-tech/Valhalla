from __future__ import annotations
from fastapi import APIRouter, HTTPException
from . import service
from .post_to_ledger import post as post_income

router = APIRouter(prefix="/core/income", tags=["core-income"])

@router.post("")
def create(name: str, amount: float, frequency: str = "monthly", next_date: str = "", currency: str = "CAD", notes: str = ""):
    try:
        return service.create(name=name, amount=amount, frequency=frequency, next_date=next_date, currency=currency, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = ""):
    return {"items": service.list_items(status=status)}

@router.post("/{income_id}/post_ledger")
def post_ledger(income_id: str, date: str, account_id: str = ""):
    try:
        return post_income(income_id=income_id, date=date, account_id=account_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")
