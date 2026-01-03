from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Tier = Literal["green", "yellow", "orange", "red"]
Action = Literal[
    "pause_expansion",
    "reduce_marketing",
    "freeze_hiring",
    "focus_boring_engines",
    "prioritize_collections",
    "raise_reserves",
    "audit_expenses",
    "review_legal_flags",
    "review_followups",
    "manual_override_required",
]


class ShieldConfig(BaseModel):
    enabled: bool = True
    tier: Tier = "green"
    reserve_floor: float = 0.0
    min_deals_pipeline: int = 0
    notes: str = ""
    actions_by_tier: Dict[Tier, List[Action]] = Field(default_factory=dict)
    updated_at: datetime


class ShieldUpdate(BaseModel):
    enabled: Optional[bool] = None
    tier: Optional[Tier] = None
    reserve_floor: Optional[float] = None
    min_deals_pipeline: Optional[int] = None
    notes: Optional[str] = None
    actions_by_tier: Optional[Dict[Tier, List[Action]]] = None


class EvaluateRequest(BaseModel):
    reserves: float = 0.0
    pipeline_deals: int = 0
    override_tier: Optional[Tier] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class EvaluateResponse(BaseModel):
    ok: bool
    tier: Tier
    enabled: bool
    triggered: bool
    actions: List[Action] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
