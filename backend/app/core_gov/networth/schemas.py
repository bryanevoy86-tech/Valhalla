from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Kind = Literal["asset", "liability"]
Status = Literal["active", "archived"]


class LineItemCreate(BaseModel):
    name: str
    kind: Kind
    status: Status = "active"
    value: float = 0.0
    currency: str = "CAD"
    category: str = "other"   # "cash", "vehicle", "tools", "debt", "mortgage", etc.
    notes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)


class LineItemRecord(BaseModel):
    id: str
    name: str
    kind: Kind
    status: Status
    value: float
    currency: str
    category: str
    notes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class LineItemListResponse(BaseModel):
    items: List[LineItemRecord]
