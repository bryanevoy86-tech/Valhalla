from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


class KnowDocCreate(BaseModel):
    title: str
    source: str = Field(default="manual")  # "vault:<id>", "upload", "manual", etc.
    tags: List[str] = Field(default_factory=list)
    content: str  # raw text content to ingest
    linked: Dict[str, str] = Field(default_factory=dict)  # e.g. {"deal_id":"..."}
    meta: Dict[str, Any] = Field(default_factory=dict)


class KnowDocRecord(BaseModel):
    id: str
    title: str
    source: str
    tags: List[str] = Field(default_factory=list)
    linked: Dict[str, str] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ChunkRecord(BaseModel):
    id: str
    doc_id: str
    ord: int
    text: str
    char_start: int
    char_end: int
    tokens_est: int
    created_at: datetime


class IngestResult(BaseModel):
    doc: KnowDocRecord
    chunks_created: int


class SearchHit(BaseModel):
    doc_id: str
    doc_title: str
    chunk_id: str
    score: float
    snippet: str
    source: str  # doc.source
    tags: List[str] = Field(default_factory=list)
    linked: Dict[str, str] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    hits: List[SearchHit] = Field(default_factory=list)


class RetrieveResponse(BaseModel):
    chunk: ChunkRecord
    doc: KnowDocRecord


class IndexStats(BaseModel):
    docs: int
    chunks: int
    terms: int
    updated_at: datetime


class RebuildResponse(BaseModel):
    ok: bool
    docs_indexed: int
    chunks_indexed: int
    stats: IndexStats


class KnowDocListResponse(BaseModel):
    items: List[KnowDocRecord]
