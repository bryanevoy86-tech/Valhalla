from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/tax_buckets", tags=["core-tax-buckets"])

@router.post("")
def create(code: str, name: str, risk: str = "safe", notes: str = ""):
    try:
        return service.create(code=code, name=name, risk=risk, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/seed")
def seed():
    return service.seed_defaults()

@router.get("")
def list_items(status: str = "active"):
    return {"items": service.list_items(status=status)}
