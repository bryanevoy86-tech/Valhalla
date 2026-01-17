from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


EngineStatus = Literal["planned", "active", "paused", "retired"]
RunStatus = Literal["open", "done", "canceled"]


class BoringEngineCreate(BaseModel):
    name: str  # "Storage Cleaning", "Landscaping", etc.
    category: str = "boring"
    status: EngineStatus = "planned"
    description: str = ""
    pricing_notes: str = ""
    target_city: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class BoringEngineRecord(BaseModel):
    id: str
    name: str
    category: str = "boring"
    status: EngineStatus
    description: str = ""
    pricing_notes: str = ""
    target_city: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class RunCreate(BaseModel):
    engine_id: str
    title: str  # job name
    status: RunStatus = "open"
    customer: str = ""
    revenue: float = 0.0
    cost: float = 0.0
    notes: str = ""
    due_date: str = ""  # keep string in v1
    meta: Dict[str, Any] = Field(default_factory=dict)


class RunRecord(BaseModel):
    id: str
    engine_id: str
    title: str
    status: RunStatus
    customer: str = ""
    revenue: float = 0.0
    cost: float = 0.0
    notes: str = ""
    due_date: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class EngineListResponse(BaseModel):
    items: List[BoringEngineRecord]


class RunListResponse(BaseModel):
    items: List[RunRecord]


class EngineSummary(BaseModel):
    engine_id: str
    name: str
    status: EngineStatus
    runs_open: int
    runs_done: int
    revenue_total: float
    profit_total: float


class SummaryResponse(BaseModel):
    engines: List[EngineSummary] = Field(default_factory=list)
