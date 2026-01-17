from __future__ import annotations
from fastapi import APIRouter
from .service import plan
from .followups import create_income_followups

router = APIRouter(prefix="/core/payday", tags=["core-payday"])

@router.get("/plan")
def get(days: int = 14):
    return plan(days=days)

@router.post("/followups")
def push(days: int = 14):
    return create_income_followups(days=days)
