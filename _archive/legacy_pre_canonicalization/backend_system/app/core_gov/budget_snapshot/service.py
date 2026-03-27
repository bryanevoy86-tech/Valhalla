from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter
from .service import snapshot

router = APIRouter(prefix="/core/budget/snapshot", tags=["core-budget-snapshot"])

@router.get("")
def get(days: int = 14):
    return snapshot(days=days)
