from __future__ import annotations

from fastapi import APIRouter
from . import service

router = APIRouter(prefix="/core/buyplan", tags=["core-buyplan"])

@router.get("/weekly")
def weekly(days: int = 7):
    return service.weekly_plan(days=days)
