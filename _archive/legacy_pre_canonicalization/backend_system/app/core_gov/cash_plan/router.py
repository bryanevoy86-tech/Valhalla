from __future__ import annotations
from fastapi import APIRouter
from .service import monthly_plan

router = APIRouter(prefix="/core/cash_plan", tags=["core-cash-plan"])

@router.get("/month/{month}")
def plan(month: str):
    return monthly_plan(month=month)
