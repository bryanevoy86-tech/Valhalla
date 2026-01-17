from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

EntityType = Literal["deal", "partner", "doc", "tx", "obligation", "property", "other"]
SourceType = Literal["doc", "url", "note", "chat", "file", "other"]


class SourceRef(BaseModel):
    source_type: SourceType = "doc"
    ref: str                          # doc_id, url, note_id, filename, etc.
    title: str = ""
    snippet: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)


class AttachRequest(BaseModel):
    entity_type: EntityType
    entity_id: str
    sources: List[SourceRef] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class LinkRecord(BaseModel):
    id: str
    entity_type: EntityType
    entity_id: str
    sources: List[SourceRef] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class LinkListResponse(BaseModel):
    items: List[LinkRecord]


class FormatCitationsRequest(BaseModel):
    sources: List[SourceRef] = Field(default_factory=list)
    style: Literal["short", "long"] = "short"


class FormatCitationsResponse(BaseModel):
    citations: List[str] = Field(default_factory=list)

class IngestText(BaseModel):
    source_title: str
    source_type: str = "note"         # note/doc/email/etc
    source_ref: str = ""              # doc_id, url, filename, etc
    text: str
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class SourceRecord(BaseModel):
    id: str
    source_title: str
    source_type: str
    source_ref: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ChunkRecord(BaseModel):
    id: str
    source_id: str
    ordinal: int
    text: str
    token_count: int
    created_at: datetime


class RetrieveRequest(BaseModel):
    query: str
    k: int = 5
    min_score: float = 0.0
    tag: str = ""                    # optional filter by source tag


class RetrieveHit(BaseModel):
    score: float
    source_id: str
    source_title: str
    source_ref: str = ""
    chunk_id: str
    ordinal: int
    snippet: str


class RetrieveResponse(BaseModel):
    query: str
    hits: List[RetrieveHit] = Field(default_factory=list)
