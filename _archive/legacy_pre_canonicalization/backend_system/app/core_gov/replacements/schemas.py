from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Priority = Literal["A", "B", "C", "D"]
Status = Literal["planned", "saving", "ready", "purchased", "archived"]


class ReplacementCreate(BaseModel):
    name: str                      # "Mattress", "Sweaters"
    target_cost: float
    currency: str = "CAD"
    priority: Priority = "B"
    status: Status = "planned"
    desired_by: str = ""           # YYYY-MM-DD
    suggested_months: int = 3      # planning horizon
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class ReplacementRecord(BaseModel):
    id: str
    name: str
    target_cost: float
    currency: str
    priority: Priority
    status: Status
    desired_by: str = ""
    suggested_months: int
    monthly_save: float = 0.0
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ReplacementListResponse(BaseModel):
    items: List[ReplacementRecord]


class PlanResponse(BaseModel):
    id: str
    name: str
    target_cost: float
    suggested_months: int
    monthly_save: float
    schedule_suggestion: List[str] = Field(default_factory=list)
