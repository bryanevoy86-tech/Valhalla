from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Status = Literal["new", "categorized", "exported", "archived"]
Source = Literal["manual", "photo", "email", "bank", "other"]


class ReceiptCreate(BaseModel):
    vendor: str
    date: str                       # "YYYY-MM-DD"
    total: float
    currency: str = "CAD"
    status: Status = "new"
    source: Source = "manual"

    # optional details
    tax: float = 0.0
    tip: float = 0.0
    payment_method: str = ""        # "debit", "visa", etc.

    # links
    doc_id: str = ""                # if stored in /core/docs
    blob_ref: str = ""              # later: photo blob reference
    notes: str = ""

    # classification
    category: str = ""              # filled by categorizer
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class ReceiptRecord(BaseModel):
    id: str
    vendor: str
    date: str
    total: float
    currency: str
    status: Status
    source: Source
    tax: float = 0.0
    tip: float = 0.0
    payment_method: str = ""
    doc_id: str = ""
    blob_ref: str = ""
    notes: str = ""
    category: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ReceiptListResponse(BaseModel):
    items: List[ReceiptRecord]
