from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, Body
from . import store, service

router = APIRouter(prefix="/core/envelopes", tags=["core-envelopes"])

@router.get("")
def get():
    return store.get()

@router.post("")
def save(payload: Dict[str, Any] = Body(...)):
    return store.save(payload or {})

@router.get("/month/{month}")
def month(month: str):
    return service.month_totals(month=month)
