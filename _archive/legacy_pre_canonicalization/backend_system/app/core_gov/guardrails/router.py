from __future__ import annotations

from fastapi import APIRouter
from . import service

router = APIRouter(prefix="/core/guardrails", tags=["core-guardrails"])

@router.get("/daily")
def daily(days_ahead: int = 7):
    return service.daily_guard(days_ahead=days_ahead)
