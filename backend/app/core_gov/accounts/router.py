from __future__ import annotations
from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/accounts", tags=["core-accounts"])

@router.post("")
def create(name: str, kind: str = "chequing", currency: str = "CAD", masked: str = "", notes: str = ""):
    try:
        return service.create(name=name, kind=kind, currency=currency, masked=masked, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "active"):
    return {"items": service.list_items(status=status)}
