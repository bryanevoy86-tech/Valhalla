from __future__ import annotations

from fastapi import APIRouter
from . import service

router = APIRouter(prefix="/core/house_reminders", tags=["core-house-reminders"])

@router.post("/followups")
def followups(days_ahead: int = 7):
    return service.create_followups(days_ahead=days_ahead)
