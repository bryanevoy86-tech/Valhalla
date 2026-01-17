from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Body, HTTPException
from . import service

router = APIRouter(prefix="/core/docs", tags=["core-document-vault"])

@router.post("")
def create(payload: Dict[str, Any] = Body(...)):
    try:
        return service.create(
            title=payload.get("title",""),
            doc_type=payload.get("doc_type","note"),
            tags=payload.get("tags") or [],
            source=payload.get("source",""),
            file_path=payload.get("file_path",""),
            text=payload.get("text",""),
            links=payload.get("links") or [],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(tag: str = "", q: str = ""):
    return {"items": service.list_items(tag=tag, q=q)}

@router.get("/{doc_id}")
def get_one(doc_id: str):
    d = service.get_one(doc_id)
    if not d:
        raise HTTPException(status_code=404, detail="not found")
    return d

@router.post("/{doc_id}/tag")
def add_tag(doc_id: str, tag: str):
    try:
        return service.add_tag(doc_id=doc_id, tag=tag)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")

@router.post("/{doc_id}/link")
def link(doc_id: str, target_type: str, target_id: str):
    try:
        return service.link(doc_id=doc_id, target_type=target_type, target_id=target_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")
