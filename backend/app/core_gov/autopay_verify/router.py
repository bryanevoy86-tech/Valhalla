from __future__ import annotations

from fastapi import APIRouter
from . import service

router = APIRouter(prefix="/core/autopay_verify", tags=["core-autopay-verify"])

@router.get("")
def verify(days_back: int = 7, days_ahead: int = 7):
    return service.verify(days_back=days_back, days_ahead=days_ahead)
