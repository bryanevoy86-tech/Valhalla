from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/bank_profiles", tags=["core-bank-profiles"])


@router.post("")
def create(name: str, mapping: Dict[str, Any], notes: str = ""):
    try:
        return service.create(name=name, mapping=mapping, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
def list_items():
    return {"items": service.list_items()}


@router.get("/{profile_id}")
def get_one(profile_id: str):
    x = service.get_one(profile_id)
    if not x:
        raise HTTPException(status_code=404, detail="profile not found")
    return x
