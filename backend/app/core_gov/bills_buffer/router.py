from __future__ import annotations

from fastapi import APIRouter
from . import service

router = APIRouter(prefix="/core/bills_buffer", tags=["core-bills-buffer"])

@router.get("")
def required(days: int = 30):
    return service.required_buffer(days=days)
