from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List
from . import service

router = APIRouter(prefix="/core/playbooks", tags=["core-playbooks"])

@router.post("")
def create(name: str, category: str, region: str = "", steps: List[str] = None, checklist: List[str] = None, notes: str = "", meta: Dict[str, Any] = None, status: str = "active"):
    try:
        return service.create(name=name, category=category, region=region, steps=steps or [], checklist=checklist or [], notes=notes, meta=meta or {}, status=status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/seed")
def seed():
    return service.seed_defaults()

@router.get("")
def list_items(status: str = "", category: str = "", region: str = "", q: str = ""):
    return {"items": service.list_items(status=status, category=category, region=region, q=q)}
