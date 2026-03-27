from __future__ import annotations

from fastapi import APIRouter
from . import service

router = APIRouter(prefix="/core/reorder_engine", tags=["core-reorder-engine"])

@router.get("")
def build():
    return service.build_reorder_list()

@router.post("/followups")
def followups(days_ahead: int = 2):
    return service.create_purchase_followups(days_ahead=days_ahead)
