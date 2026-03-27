from __future__ import annotations
from fastapi import APIRouter
from .service import forecast
from .buffer import with_buffer

router = APIRouter(prefix="/core/cashflow", tags=["core-cashflow"])

@router.get("")
def get(days: int = 30):
    return forecast(days=days)

@router.get("/with_buffer")
def with_buffer_ep(days: int = 30, buffer_min: float = 500.0):
    return with_buffer(days=days, buffer_min=buffer_min)
