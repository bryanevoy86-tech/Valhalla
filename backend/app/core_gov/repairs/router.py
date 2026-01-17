from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/repairs", tags=["core-repairs"])

@router.post("")
def create(property_id: str, title: str = "Repair Worksheet", line_items: List[Dict[str, Any]] = None, notes: str = "", meta: Dict[str, Any] = None):
    try:
        return service.create(property_id=property_id, title=title, line_items=line_items or [], notes=notes, meta=meta or {})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_by_property(property_id: str):
    return {"items": service.list_by_property(property_id=property_id)}

@router.get("/summary")
def summary(property_id: str):
    return service.summarize(property_id=property_id)
