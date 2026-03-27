from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/rents", tags=["core-rents"])

@router.post("")
def create(property_id: str, gross_rent: float = 0.0, other_income: float = 0.0, expenses_monthly: Dict[str, float] = None, loan_pmt_monthly: float = 0.0, notes: str = "", meta: Dict[str, Any] = None):
    try:
        return service.create(property_id=property_id, gross_rent=gross_rent, other_income=other_income, expenses_monthly=expenses_monthly or {}, loan_pmt_monthly=loan_pmt_monthly, notes=notes, meta=meta or {})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_by_property(property_id: str):
    return {"items": service.list_by_property(property_id=property_id)}

@router.get("/summary")
def summary(property_id: str):
    return service.summarize(property_id=property_id)
