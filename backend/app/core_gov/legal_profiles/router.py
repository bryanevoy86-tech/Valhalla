from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Body, HTTPException
from . import service

router = APIRouter(prefix="/core/legal/jurisdictions", tags=["core-legal-jurisdictions"])

@router.post("")
def create(payload: Dict[str, Any] = Body(...)):
    try:
        return service.create(
            jurisdiction=payload.get("jurisdiction",""),
            country=payload.get("country",""),
            kind=payload.get("kind","province"),
            notes=payload.get("notes",""),
            rules=payload.get("rules") or {},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(country: str = ""):
    return {"items": service.list_items(country=country)}

@router.get("/{code}")
def get_one(code: str):
    x = service.get_by_code(code)
    if not x:
        raise HTTPException(status_code=404, detail="not found")
    return x
