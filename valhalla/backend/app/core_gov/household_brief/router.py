from __future__ import annotations
from fastapi import APIRouter
from .service import build

router = APIRouter(prefix="/core/household/brief", tags=["core-household-brief"])

@router.get("")
def get(days_bills: int = 14):
    return build(days_bills=days_bills)
