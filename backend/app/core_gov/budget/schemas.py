from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


BucketType = Literal["essentials", "variable", "sinking", "fun", "savings", "other"]
Status = Literal["active", "paused", "archived"]
Priority = Literal["A", "B", "C", "D"]


class BucketCreate(BaseModel):
    name: str                      # "Groceries", "Fuel", "Kids", "Fun"
    bucket_type: BucketType = "variable"
    status: Status = "active"
    priority: Priority = "B"
    monthly_limit: float = 0.0     # 0 means "informational only"
    rollover: bool = False
    currency: str = "CAD"
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class BucketRecord(BaseModel):
    id: str
    name: str
    bucket_type: BucketType
    status: Status
    priority: Priority
    monthly_limit: float
    rollover: bool
    currency: str
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class BucketListResponse(BaseModel):
    items: List[BucketRecord]


class MonthSnapshot(BaseModel):
    month: str                     # YYYY-MM
    bucket_id: str
    allocated: float = 0.0         # optional manual allocation
    spent: float = 0.0
    remaining: float = 0.0
    updated_at: datetime


class MonthSnapshotResponse(BaseModel):
    items: List[MonthSnapshot]
