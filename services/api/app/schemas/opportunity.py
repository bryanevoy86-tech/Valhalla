"""
PACK CI2: Opportunity Engine Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class OpportunityIn(BaseModel):
    source_type: str
    source_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    value_score: float = 0.0
    effort_score: float = 0.0
    risk_score: float = 0.0
    roi_score: float = 0.0
    time_horizon_days: Optional[int] = None
    tags: Optional[Dict[str, Any]] = None
    active: bool = True


class OpportunityOut(OpportunityIn):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OpportunityList(BaseModel):
    total: int
    items: List[OpportunityOut]
