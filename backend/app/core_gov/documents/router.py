from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from . import service

router = APIRouter(prefix="/core/documents", tags=["core-documents"])

@router.post("")
def create(title: str, doc_type: str = "general", tags: List[str] = None, local_path: str = "", source: str = "manual", notes: str = ""):
    try:
        return service.create(title=title, doc_type=doc_type, tags=tags, local_path=local_path, source=source, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "", doc_type: str = "", tag: str = "", q: str = ""):
    return {"items": service.list_items(status=status, doc_type=doc_type, tag=tag, q=q)}

@router.get("/{doc_id}")
def get_one(doc_id: str):
    x = service.get_one(doc_id)
    if not x:
        raise HTTPException(status_code=404, detail="doc not found")
    return x

@router.patch("/{doc_id}")
def patch(doc_id: str, patch: Dict[str, Any]):
    try:
        return service.patch(doc_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="doc not found")
