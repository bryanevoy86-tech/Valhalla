from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


RunType = Literal["nightly", "manual", "weekly"]


class RunRequest(BaseModel):
    run_type: RunType = "manual"
    month: str = ""  # optionally "YYYY-MM" for budget snapshot
    meta: Dict[str, Any] = Field(default_factory=dict)


class RunRecord(BaseModel):
    id: str
    run_type: RunType
    created_at: datetime
    meta: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    results: Dict[str, Any] = Field(default_factory=dict)


class RunListResponse(BaseModel):
    items: List[RunRecord]
