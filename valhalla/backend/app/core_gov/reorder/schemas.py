from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Status = Literal["active", "paused", "archived"]


class ReorderRuleCreate(BaseModel):
    inventory_id: str
    status: Status = "active"
    reorder_qty: float = 1.0
    cooldown_days: int = 7
    store_hint: str = ""
    category: str = "household"
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class ReorderRuleRecord(BaseModel):
    id: str
    inventory_id: str
    status: Status
    reorder_qty: float
    cooldown_days: int
    store_hint: str = ""
    category: str = "household"
    last_triggered_at: str = ""
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class RuleListResponse(BaseModel):
    items: List[ReorderRuleRecord]


class EvalResponse(BaseModel):
    ok: bool
    triggered: int = 0
    created_shopping: int = 0
    results: List[Dict[str, Any]] = Field(default_factory=list)
