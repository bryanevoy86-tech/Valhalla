from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, Body, HTTPException
from . import service
from .bundles import create as create_bundle, get as get_bundle, list_bundles
from .export_manifest import manifest
from .ingest import enqueue

router = APIRouter(prefix="/core/docs", tags=["core-doc-vault"])

@router.post("")
def create(title: str, kind: str = "note", file_path: str = "", tags: List[str] = Body(default=[]), links: Dict[str, str] = Body(default={}), notes: str = ""):
    try:
        return service.create(title=title, kind=kind, file_path=file_path, tags=tags or [], links=links or {}, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_docs(tag: str = "", kind: str = "", status: str = "active", limit: int = 100):
    return {"docs": service.list_docs(tag=tag, kind=kind, status=status, limit=limit)}

@router.get("/{doc_id}")
def get(doc_id: str):
    d = service.get(doc_id)
    if not d:
        raise HTTPException(status_code=404, detail="not found")
    return d

@router.patch("/{doc_id}")
def patch(doc_id: str, payload: Dict[str, Any] = Body(...)):
    try:
        return service.patch(doc_id, payload or {})
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")

@router.post("/bundles")
def bundle_create(name: str, doc_ids: List[str] = Body(default=[]), links: Dict[str, str] = Body(default={})):
    try:
        return create_bundle(name=name, doc_ids=doc_ids or [], links=links or {})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/bundles")
def bundle_list():
    return {"bundles": list_bundles()}

@router.get("/bundles/{bundle_id}")
def bundle_get(bundle_id: str):
    b = get_bundle(bundle_id)
    if not b:
        raise HTTPException(status_code=404, detail="not found")
    return b

@router.get("/bundles/{bundle_id}/manifest")
def bundle_manifest(bundle_id: str):
    return manifest(bundle_id=bundle_id)

@router.post("/{doc_id}/enqueue_knowledge")
def enqueue_knowledge(doc_id: str):
    return enqueue(doc_id=doc_id)
