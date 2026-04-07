"""
PACK CI1: Decision Recommendation Engine Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DecisionContextIn(BaseModel):
    source: str = Field("heimdall", description="Who requested the recommendation.")
    mode: str = Field("growth", description="Strategic mode: growth, war, recovery, family, etc.")
    context_data: Dict[str, Any]


class DecisionContextOut(DecisionContextIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DecisionRecommendationIn(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    leverage_score: float = 0.0
    risk_score: float = 0.0
    urgency_score: float = 0.0
    alignment_score: float = 0.0
    reasoning: Optional[str] = None


class DecisionRecommendationOut(DecisionRecommendationIn):
    id: int
    context_id: int
    priority_rank: int
    recommended: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DecisionRecommendationList(BaseModel):
    context: DecisionContextOut
    items: List[DecisionRecommendationOut]
