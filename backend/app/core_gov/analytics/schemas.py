from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Snapshot(BaseModel):
    id: str
    created_at: datetime
    metrics: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class SnapshotResponse(BaseModel):
    snapshot: Snapshot


class SnapshotListResponse(BaseModel):
    items: List[Snapshot]
