from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException

from .schemas import DocCreate, DocListResponse, BundleRequest, BundleResponse
from . import service, bridge

router = APIRouter(prefix="/core/docs", tags=["core-docs"])


@router.post("")
def create_doc(payload: DocCreate):
    try:
        return service.create_doc(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=DocListResponse)
def list_docs(
    doc_type: Optional[str] = None,
    visibility: Optional[str] = None,
    tag: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
):
    return {"items": service.list_docs(doc_type=doc_type, visibility=visibility, tag=tag, entity_type=entity_type, entity_id=entity_id)}


@router.get("/{doc_id}")
def get_doc(doc_id: str):
    d = service.get_doc(doc_id)
    if not d:
        raise HTTPException(status_code=404, detail="doc not found")
    return d


@router.patch("/{doc_id}")
def patch_doc(doc_id: str, patch: Dict[str, Any]):
    try:
        return service.patch_doc(doc_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="doc not found")


@router.post("/bundle", response_model=BundleResponse)
def bundle(payload: BundleRequest):
    try:
        return service.create_bundle(
            name=payload.name,
            doc_ids=payload.doc_ids,
            include_links=payload.include_links,
            include_notes=payload.include_notes,
            meta=payload.meta,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{doc_id}/attach_to_knowledge")
def attach_to_knowledge(doc_id: str, title: str = "", snippet: str = ""):
    doc = service.get_doc(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="doc not found")
    return bridge.attach_doc_as_source(doc, title=title, snippet=snippet)


@router.post("/bundle_shareable")
def bundle_shareable(payload: BundleRequest, level: str = "shareable"):
    try:
        b = service.create_bundle(
            name=payload.name,
            doc_ids=payload.doc_ids,
            include_links=payload.include_links,
            include_notes=payload.include_notes,
            meta=payload.meta,
        )
        return bridge.sanitize_manifest(b, level=level)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

