from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class MonthlyReportRequest(BaseModel):
    month: str                      # "YYYY-MM"
    include_details: bool = False
    meta: Dict[str, Any] = Field(default_factory=dict)


class MonthlyReportRecord(BaseModel):
    id: str
    month: str
    created_at: datetime
    meta: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    report: Dict[str, Any] = Field(default_factory=dict)


class MonthlyReportListResponse(BaseModel):
    items: List[MonthlyReportRecord]
