from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


# Research Sources
class SourceIn(BaseModel):
    name: str = Field(..., max_length=255)
    url: str = Field(..., max_length=2048)
    kind: str = Field(default="web", max_length=50)
    ttl_seconds: int = Field(default=86400, ge=0)
    enabled: bool = True


class SourceOut(BaseModel):
    id: int
    name: str
    url: str
    kind: str
    ttl_seconds: int
    enabled: bool
    created_at: datetime
    last_ingested_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Research Docs
class DocOut(BaseModel):
    id: int
    source_id: int
    title: Optional[str] = None
    url: Optional[str] = None
    content: str
    chunk_index: int
    ingested_at: datetime

    class Config:
        from_attributes = True


# Ingest Request
class IngestIn(BaseModel):
    source_id: int


class IngestOut(BaseModel):
    ok: bool
    source_id: int
    doc_count: int
    message: str


# Query Request
class QueryIn(BaseModel):
    q: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=50)


class QueryResult(BaseModel):
    source_name: str
    doc_id: int
    title: Optional[str] = None
    url: Optional[str] = None
    snippet: str
    relevance_score: float = 0.0


class QueryOut(BaseModel):
    query: str
    result_count: int
    results: list[QueryResult]


# Playbooks
class PlaybookIn(BaseModel):
    slug: str = Field(..., max_length=255)
    title: str = Field(..., max_length=512)
    body_md: str
    tags: Optional[str] = Field(None, max_length=512)
    enabled: bool = True


class PlaybookOut(BaseModel):
    id: int
    slug: str
    title: str
    body_md: str
    tags: Optional[str] = None
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Embeddings & Semantic Search
class EmbeddingUpsertIn(BaseModel):
    doc_id: int
    vector: list[float]  # same dimensionality across all docs


class SemanticQueryIn(BaseModel):
    q: Optional[str] = None  # optional raw text (ignored in this simple API)
    top_k: int = Field(default=5, ge=1, le=50)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    vector: Optional[list[float]] = None  # Either provide a fresh vector, or the server will error if none provided


class SemanticHit(BaseModel):
    doc_id: int
    url: Optional[str] = None
    title: Optional[str] = None
    score: float
    preview: str


class SemanticQueryOut(BaseModel):
    hits: list[SemanticHit]
