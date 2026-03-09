from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


EntityType = Literal["deal", "partner", "tx", "obligation", "property", "loan", "grant", "other"]
DocType = Literal["receipt", "contract", "id", "invoice", "statement", "photo", "note", "other"]
Visibility = Literal["internal", "shareable", "private"]


class DocCreate(BaseModel):
    title: str
    doc_type: DocType = "other"
    visibility: Visibility = "internal"
    file_path: str = ""               # local path on server (v1)
    blob_ref: str = ""                # future (s3, gdrive, etc)
    mime: str = ""
    sha256: str = ""                  # optional if you compute later
    tags: List[str] = Field(default_factory=list)
    links: Dict[str, str] = Field(default_factory=dict)  # entity_type -> entity_id
    notes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)


class DocRecord(BaseModel):
    id: str
    title: str
    doc_type: DocType
    visibility: Visibility
    file_path: str = ""
    blob_ref: str = ""
    mime: str = ""
    sha256: str = ""
    tags: List[str] = Field(default_factory=list)
    links: Dict[str, str] = Field(default_factory=dict)
    notes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class DocListResponse(BaseModel):
    items: List[DocRecord]


class BundleRequest(BaseModel):
    name: str
    doc_ids: List[str] = Field(default_factory=list)
    include_links: bool = True
    include_notes: bool = True
    meta: Dict[str, Any] = Field(default_factory=dict)


class BundleResponse(BaseModel):
    id: str
    name: str
    manifest: Dict[str, Any] = Field(default_factory=dict)
