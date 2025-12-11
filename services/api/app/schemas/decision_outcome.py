"""
PACK CL9: Decision Outcome Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DecisionOutcomeBase(BaseModel):
    decision_id: str = Field(..., description="Internal ID tying back to the original recommendation.")
    title: str = Field(..., description="Short human-readable description of the decision.")
    domain: str = Field(..., description="Domain like 'real_estate', 'arbitrage', 'family', 'security', etc.")
    action_taken: str = Field(
        ...,
        description="What Bryan actually did: 'accepted', 'ignored', 'partial', 'blocked', 'overridden'."
    )
    outcome_quality: Optional[str] = Field(
        default=None,
        description="High-level quality label: 'good', 'neutral', 'bad', etc."
    )
    impact_score: Optional[int] = Field(
        default=None,
        description="Rough numeric impact (-100 to +100)."
    )
    notes: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class DecisionOutcomeCreate(DecisionOutcomeBase):
    occurred_at: Optional[datetime] = Field(
        default=None,
        description="When the outcome happened (if known).",
    )


class DecisionOutcomeOut(DecisionOutcomeBase):
    id: int
    created_at: datetime
    occurred_at: Optional[datetime]
    updated_at: datetime

    class Config:
        from_attributes = True


class DecisionOutcomeList(BaseModel):
    total: int
    items: List[DecisionOutcomeOut]
