from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from .schemas import (
    KnowDocCreate,
    IngestResult,
    SearchResponse,
    RetrieveResponse,
    KnowDocListResponse,
    RebuildResponse,
    IndexStats,
)
from . import service, store

router = APIRouter(prefix="/know", tags=["core-know"])


@router.post("/ingest", response_model=IngestResult)
def ingest(payload: KnowDocCreate):
    r = service.ingest_doc(
        title=payload.title,
        source=payload.source,
        tags=payload.tags,
        content=payload.content,
        linked=payload.linked,
        meta=payload.meta,
    )
    return r


@router.post("/ingest_inbox")
def ingest_inbox(limit: int = Query(default=25, ge=1, le=200)):
    return service.ingest_inbox_files(limit=limit)


@router.get("/docs", response_model=KnowDocListResponse)
def list_docs(tag: Optional[str] = None):
    items = store.list_docs()
    if tag:
        items = [d for d in items if tag in (d.get("tags") or [])]
    return {"items": items}


@router.get("/docs/{doc_id}")
def get_doc(doc_id: str):
    d = service.get_doc(doc_id)
    if not d:
        raise HTTPException(status_code=404, detail="knowledge doc not found")
    return d


@router.get("/chunks/{chunk_id}", response_model=RetrieveResponse)
def get_chunk(chunk_id: str):
    c = service.get_chunk(chunk_id)
    if not c:
        raise HTTPException(status_code=404, detail="chunk not found")
    d = service.get_doc(c["doc_id"])
    if not d:
        raise HTTPException(status_code=404, detail="doc missing for chunk")
    return {"chunk": c, "doc": d}


@router.get("/search", response_model=SearchResponse)
def search(q: str = Query(..., min_length=1), limit: int = Query(default=10, ge=1, le=50), tag: Optional[str] = None):
    hits = service.search(query=q, limit=limit, tag=tag)
    return {"query": q, "hits": hits}


@router.post("/rebuild_index", response_model=RebuildResponse)
def rebuild_index():
    r = service.rebuild_index()
    idx = store.read_index()
    stats = {
        "docs": len(store.list_docs()),
        "chunks": len(store.list_chunks()),
        "terms": len(idx.get("terms", {})),
        "updated_at": idx.get("updated_at"),
    }
    return {"ok": True, "docs_indexed": r["docs_indexed"], "chunks_indexed": r["chunks_indexed"], "stats": stats}
