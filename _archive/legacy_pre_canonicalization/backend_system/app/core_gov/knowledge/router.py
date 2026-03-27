from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Optional

from .schemas import AttachRequest, LinkListResponse, FormatCitationsRequest, FormatCitationsResponse
from . import service

router = APIRouter(prefix="/core/knowledge", tags=["core-knowledge"])


@router.post("/attach")
def attach(payload: AttachRequest):
    try:
        return service.attach(
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            sources=[s.model_dump() for s in payload.sources],
            tags=payload.tags,
            meta=payload.meta,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/links", response_model=LinkListResponse)
def list_links(entity_type: Optional[str] = None, entity_id: Optional[str] = None):
    return {"items": service.list_links(entity_type=entity_type, entity_id=entity_id)}


@router.post("/citations/format", response_model=FormatCitationsResponse)
def format_citations(payload: FormatCitationsRequest):
    return {"citations": service.format_citations([s.model_dump() for s in payload.sources], style=payload.style)}
