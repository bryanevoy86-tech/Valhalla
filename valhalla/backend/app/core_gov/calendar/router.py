from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter

from . import service

router = APIRouter(prefix="/core/calendar", tags=["core-calendar"])


@router.get("/feed")
def get_feed(days: int = 30) -> Dict[str, Any]:
    return service.feed(days=days)
