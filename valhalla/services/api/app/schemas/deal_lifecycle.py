# services/api/app/schemas/deal_lifecycle.py

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class LifecycleStep(BaseModel):
    name: str
    status: str  # pending, running, completed, failed
    notes: Optional[str] = None


class DealLifecycleSummary(BaseModel):
    backend_deal_id: int
    steps: List[LifecycleStep]
    current_stage: str
    next_recommended_stage: Optional[str] = None
    automated_actions_available: List[str] = Field(
        default_factory=list,
        description="Actions Heimdall is allowed to perform automatically."
    )


class RunLifecycleActionRequest(BaseModel):
    backend_deal_id: int
    action: str  # e.g. "run_underwriting", "match_buyers", "prepare_closing", "notify_parties", "profit_allocation"


class RunLifecycleActionResponse(BaseModel):
    backend_deal_id: int
    action: str
    status: str
    message: str
    output: Optional[dict] = None
