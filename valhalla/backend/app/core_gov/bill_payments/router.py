from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/bill_payments", tags=["core-bill-payments"])

# Convenience endpoints
@router.get("/upcoming")
def upcoming(days: int = 14):
    from .convenience import upcoming as upcoming_bills
    return upcoming_bills(days=days)

@router.post("/mark_paid")
def mark_paid_endpoint(obligation_id: str, date: str, amount: float):
    from .convenience import mark_paid_by_obligation
    return mark_paid_by_obligation(obligation_id=obligation_id, date=date, amount=amount)

@router.post("")
def mark_paid(
    obligation_id: str,
    paid_date: str,
    amount: float,
    method: str = "manual",
    account_id: str = "",
    ledger_id: str = "",
    receipt_id: str = "",
    doc_id: str = "",
    confirmation: str = "",
    notes: str = "",
):
    try:
        return service.mark_paid(
            obligation_id=obligation_id, paid_date=paid_date, amount=amount, method=method,
            account_id=account_id, ledger_id=ledger_id, receipt_id=receipt_id, doc_id=doc_id,
            confirmation=confirmation, notes=notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(obligation_id: str = "", date_from: str = "", date_to: str = ""):
    return {"items": service.list_items(obligation_id=obligation_id, date_from=date_from, date_to=date_to)}
