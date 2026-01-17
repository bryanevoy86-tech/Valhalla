from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/allocation_engine", tags=["core-allocation-engine"])

@router.get("/preview")
def preview(rule_id: str, amount: float):
    return service.preview(rule_id=rule_id, amount=amount)

@router.post("/apply")
def apply(rule_id: str, amount: float, date: str, income_description: str = "Payday", account_id: str = ""):
    if not date:
        raise HTTPException(status_code=400, detail="date required (YYYY-MM-DD)")
    return service.apply(rule_id=rule_id, amount=amount, date=date, income_description=income_description, account_id=account_id)
