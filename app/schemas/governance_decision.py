from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class GovernanceDecisionIn(BaseModel):
    subject_type: str  # "deal", "contract", "professional"
    subject_id: int
    role: str  # "King", "Queen", "Odin", "Loki", "Tyr", etc.
    action: str  # "approve", "deny", "override", "flag"
    reason: Optional[str] = None
    is_final: bool = False


class GovernanceDecisionOut(GovernanceDecisionIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
