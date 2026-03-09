from __future__ import annotations

from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/document_links", tags=["core-document-links"])

@router.post("")
def create_link(doc_id: str, entity_type: str, entity_id: str, relation: str = "attachment", notes: str = ""):
    try:
        return service.link(doc_id=doc_id, entity_type=entity_type, entity_id=entity_id, relation=relation, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_links(entity_type: str = "", entity_id: str = "", doc_id: str = ""):
    return {"items": service.list_links(entity_type=entity_type, entity_id=entity_id, doc_id=doc_id)}
