from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException

from .schemas import EntityCreate, EntityListResponse, StatusSummary
from . import service

router = APIRouter(prefix="/core/trust", tags=["core-trust"])


@router.post("/entities")
def create_entity(payload: EntityCreate):
    try:
        return service.create_entity(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/entities", response_model=EntityListResponse)
def list_entities(
    status: Optional[str] = None,
    country: Optional[str] = None,
    entity_type: Optional[str] = None,
    tag: Optional[str] = None,
):
    return {"items": service.list_entities(status=status, country=country, entity_type=entity_type, tag=tag)}


@router.get("/entities/{entity_id}")
def get_entity(entity_id: str):
    e = service.get_entity(entity_id)
    if not e:
        raise HTTPException(status_code=404, detail="entity not found")
    return e


@router.patch("/entities/{entity_id}")
def patch_entity(entity_id: str, patch: Dict[str, Any]):
    try:
        return service.patch_entity(entity_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="entity not found")


@router.post("/entities/{entity_id}/milestones/upsert")
def upsert_milestone(entity_id: str, milestone: Dict[str, Any]):
    try:
        return service.upsert_milestone(entity_id, milestone)
    except KeyError:
        raise HTTPException(status_code=404, detail="entity not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/summary", response_model=StatusSummary)
def summary():
    return service.summary()
