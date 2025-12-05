# services/api/app/schemas/governance_decision.py

from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class GovernanceDecisionIn(BaseModel):
    subject_type: str = Field(..., description="Type: deal, contract, professional, etc.")
    subject_id: int = Field(..., description="ID of the subject being decided upon")
    role: str = Field(..., description="Decision role: King, Queen, Odin, Loki, Tyr, etc.")
    action: str = Field(..., description="Action: approve, deny, override, flag")
    reason: Optional[str] = Field(None, description="Reason for the decision")
    is_final: bool = Field(default=False, description="Is this a final binding decision?")


class GovernanceDecisionOut(GovernanceDecisionIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
