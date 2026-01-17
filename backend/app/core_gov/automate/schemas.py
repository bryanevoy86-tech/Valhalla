from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


RuleStatus = Literal["active", "paused", "archived"]
TriggerType = Literal[
    "obligations_not_covered",
    "shopping_backlog_over",
    "followups_backlog_over",
    "autopay_unverified_over",
]
ActionType = Literal[
    "create_followup",
    "create_alert",
]


class RuleCreate(BaseModel):
    name: str
    status: RuleStatus = "active"
    trigger: TriggerType
    threshold: float = 0.0
    action: ActionType
    action_payload: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class RuleRecord(BaseModel):
    id: str
    name: str
    status: RuleStatus
    trigger: TriggerType
    threshold: float
    action: ActionType
    action_payload: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class RuleListResponse(BaseModel):
    items: List[RuleRecord]


class EvalResponse(BaseModel):
    ok: bool
    triggered: int = 0
    actions_executed: int = 0
    results: List[Dict[str, Any]] = Field(default_factory=list)
