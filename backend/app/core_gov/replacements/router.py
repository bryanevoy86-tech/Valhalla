from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException

from .schemas import ReplacementCreate, ReplacementListResponse
from . import service

router = APIRouter(prefix="/core/replacements", tags=["core-replacements"])


@router.post("")
def create(payload: ReplacementCreate):
    try:
        return service.create_replacement(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ReplacementListResponse)
def list_all(status: Optional[str] = None, priority: Optional[str] = None):
    return {"items": service.list_replacements(status=status, priority=priority)}


@router.get("/{rid}")
def get_one(rid: str):
    r = service.get_replacement(rid)
    if not r:
        raise HTTPException(status_code=404, detail="replacement not found")
    return r


@router.patch("/{rid}")
def patch(rid: str, patch: Dict[str, Any]):
    try:
        return service.patch_replacement(rid, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="replacement not found")


@router.get("/{rid}/plan")
def plan(rid: str):
    try:
        return service.plan(rid)
    except KeyError:
        raise HTTPException(status_code=404, detail="replacement not found")
