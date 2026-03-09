from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Status = Literal["not_started", "in_progress", "done", "blocked"]
EntityType = Literal["corp", "llc", "sole_prop", "trust", "bank", "insurance", "other"]


class Milestone(BaseModel):
    key: str  # unique per entity (e.g. "incorporated", "bank_opened")
    title: str
    status: Status = "not_started"
    due_date: str = ""
    notes: str = ""
    updated_at: Optional[datetime] = None


class EntityCreate(BaseModel):
    name: str
    entity_type: EntityType = "trust"
    country: Literal["CA", "US", "PA", "BS", "PH", "NZ", "AE", "UK", "OTHER"] = "CA"
    region: str = ""  # province/state/zone code
    description: str = ""
    status: Status = "not_started"
    tags: List[str] = Field(default_factory=list)
    milestones: List[Milestone] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class EntityRecord(BaseModel):
    id: str
    name: str
    entity_type: EntityType
    country: str
    region: str = ""
    description: str = ""
    status: Status
    tags: List[str] = Field(default_factory=list)
    milestones: List[Milestone] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class EntityListResponse(BaseModel):
    items: List[EntityRecord]


class StatusSummary(BaseModel):
    totals: Dict[str, int] = Field(default_factory=dict)
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_country: Dict[str, int] = Field(default_factory=dict)
    blocked: List[EntityRecord] = Field(default_factory=list)
