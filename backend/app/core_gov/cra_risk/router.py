from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, Body
from . import store
from .scan import scan as scan_month

router = APIRouter(prefix="/core/cra/risk", tags=["core-cra-risk"])

@router.get("")
def get():
    return store.get()

@router.post("")
def save(payload: Dict[str, Any] = Body(...)):
    return store.save(payload or {})

@router.get("/scan/{month}")
def scan(month: str):
    return scan_month(month=month)
