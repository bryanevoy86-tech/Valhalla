"""
Schemas for buyer candidates and deal-buyer matches.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class BuyerCandidateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    email: Optional[str] = Field(None, max_length=160)
    phone: Optional[str] = Field(None, max_length=20)
    buy_box: Optional[str] = Field(None, description="JSON string describing buying criteria")
    notes: Optional[str] = None


class BuyerCandidateOut(BuyerCandidateIn):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DealBuyerMatchIn(BaseModel):
    buyer_id: int = Field(..., description="ID of the buyer candidate")
    match_status: str = Field("candidate", description="candidate | contacted | interested | passed | assigned")
    notes: Optional[str] = None


class DealBuyerMatchOut(DealBuyerMatchIn):
    id: int
    deal_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
