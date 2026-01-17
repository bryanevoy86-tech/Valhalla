from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Body, HTTPException
from . import service

router = APIRouter(prefix="/core/allocation_rules", tags=["core-allocation-rules"])

@router.post("")
def create(payload: Dict[str, Any] = Body(...)):
    try:
        return service.create(name=payload.get("name",""), splits=payload.get("splits") or [], notes=payload.get("notes",""), meta=payload.get("meta") or {})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "active"):
    return {"items": service.list_items(status=status)}
