"""
PACK X: Wholesaling Engine Schemas
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class WholesaleActivityLogIn(BaseModel):
    event_type: str = Field(..., description="call, text, offer, note, etc.")
    description: Optional[str] = None
    created_by: Optional[str] = None


class WholesaleActivityLogOut(WholesaleActivityLogIn):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class WholesalePipelineBase(BaseModel):
    deal_id: Optional[int] = None
    property_id: Optional[int] = None
    stage: str = Field(
        default="lead",
        description="lead, offer_made, under_contract, assigned, closed, dead",
    )
    lead_source: Optional[str] = None
    seller_motivation: Optional[str] = None
    arv_estimate: Optional[float] = None
    max_allowable_offer: Optional[float] = None
    assignment_fee_target: Optional[float] = None
    expected_spread: Optional[float] = None
    notes: Optional[str] = None


class WholesalePipelineCreate(WholesalePipelineBase):
    pass


class WholesalePipelineUpdate(BaseModel):
    stage: Optional[str] = None
    arv_estimate: Optional[float] = None
    max_allowable_offer: Optional[float] = None
    assignment_fee_target: Optional[float] = None
    expected_spread: Optional[float] = None
    notes: Optional[str] = None


class WholesalePipelineOut(WholesalePipelineBase):
    id: int
    created_at: datetime
    updated_at: datetime
    activities: List[WholesaleActivityLogOut] = []

    class Config:
        from_attributes = True
