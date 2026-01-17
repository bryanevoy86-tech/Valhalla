from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service
from .due import upcoming
from .followups import create_due_followups

router = APIRouter(prefix="/core/budget/obligations", tags=["core-budget-obligations"])

@router.post("")
def create(
    name: str,
    amount: float,
    cadence: str,
    due_day: int = 1,
    due_months: int = 1,
    start_date: str = "",
    pay_to: str = "",
    category: str = "household",
    account_hint: str = "",
    autopay_status: str = "unknown",
    notes: str = "",
):
    try:
        return service.create(
            name=name, amount=amount, cadence=cadence, due_day=due_day, due_months=due_months,
            start_date=start_date, pay_to=pay_to, category=category, account_hint=account_hint,
            autopay_status=autopay_status, notes=notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "", category: str = "", q: str = ""):
    return {"items": service.list_items(status=status, category=category, q=q)}

@router.get("/upcoming")
def upcoming_bills(days: int = 14, today: str = ""):
    return upcoming(days=days, today=today)

@router.post("/due_followups")
def due_followups(days: int = 7):
    return create_due_followups(days=days)
