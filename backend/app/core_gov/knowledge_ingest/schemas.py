from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Stage = Literal["inbox", "cleaned", "chunked", "indexed"]


class InboxItemCreate(BaseModel):
    title: str
    source_type: Literal["doc", "note", "chat", "url", "file"] = "note"
    source_ref: str = ""              # doc_id, url, etc.
    raw_text: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class InboxItemRecord(BaseModel):
    id: str
    title: str
    source_type: str
    source_ref: str = ""
    raw_text: str = ""
    cleaned_text: str = ""
    stage: Stage
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class InboxListResponse(BaseModel):
    items: List[InboxItemRecord]


class ProcessRequest(BaseModel):
    item_id: str
    action: Literal["clean", "chunk", "index", "all"] = "all"
    max_chunk_chars: int = 900
    overlap_chars: int = 120


class ChunkRecord(BaseModel):
    id: str
    item_id: str
    chunk_index: int
    text: str
    tokens_approx: int = 0
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class SearchRequest(BaseModel):
    query: str
    top_k: int = 8
    item_id: str = ""                 # optional scope
    tag: str = ""


class SearchHit(BaseModel):
    item_id: str
    chunk_id: str
    score: float
    title: str = ""
    source_type: str = ""
    source_ref: str = ""
    snippet: str = ""


class SearchResponse(BaseModel):
    query: str
    hits: List[SearchHit] = Field(default_factory=list)
