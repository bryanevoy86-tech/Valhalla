from __future__ import annotations

from fastapi import APIRouter
from . import service

router = APIRouter(prefix="/core/budget_calendar", tags=["core-budget-calendar"])

@router.get("/project")
def project(days_ahead: int = 45, from_date: str = ""):
    return service.project(days_ahead=days_ahead, from_date=from_date)

@router.post("/followups")
def create_followups(days_ahead: int = 14):
    return service.create_followups_for_window(days_ahead=days_ahead)
