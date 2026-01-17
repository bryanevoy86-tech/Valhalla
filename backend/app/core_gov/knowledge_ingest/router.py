from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Optional

from .schemas import InboxItemCreate, InboxListResponse, ProcessRequest, SearchRequest, SearchResponse
from . import service

router = APIRouter(prefix="/core/knowledge_ingest", tags=["core-knowledge-ingest"])


@router.post("/inbox")
def create_inbox(payload: InboxItemCreate):
    try:
        return service.create_inbox(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/inbox", response_model=InboxListResponse)
def list_inbox(stage: Optional[str] = None, tag: Optional[str] = None):
    return {"items": service.list_inbox(stage=stage, tag=tag)}


@router.get("/inbox/{item_id}")
def get_inbox(item_id: str):
    x = service.get_inbox(item_id)
    if not x:
        raise HTTPException(status_code=404, detail="item not found")
    return x


@router.post("/process")
def process(payload: ProcessRequest):
    try:
        return service.process(
            item_id=payload.item_id,
            action=payload.action,
            max_chunk_chars=payload.max_chunk_chars,
            overlap_chars=payload.overlap_chars,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="item not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest):
    try:
        return service.search(query=payload.query, top_k=payload.top_k, item_id=payload.item_id, tag=payload.tag)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
