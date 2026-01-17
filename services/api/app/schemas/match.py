"""
Buyer matching schemas for deal-to-buyer intelligence.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

class BuyerIn(BaseModel):
    name: str = Field(..., max_length=160)
    email: Optional[str] = None
    phone: Optional[str] = None
    regions: Optional[str] = None
    property_types: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_beds: Optional[int] = None
    min_baths: Optional[int] = None
    tags: Optional[str] = None
    active: bool = True

class BuyerOut(BuyerIn):
    id: int
    model_config = ConfigDict(from_attributes=True)

class DealBriefIn(BaseModel):
    headline: str
    region: Optional[str] = None
    property_type: Optional[str] = None
    price: Optional[float] = None
    beds: Optional[int] = None
    baths: Optional[int] = None
    notes: Optional[str] = None
    status: str = "active"

class DealBriefOut(DealBriefIn):
    id: int
    model_config = ConfigDict(from_attributes=True)

class MatchComputeIn(BaseModel):
    deal_id: Optional[int] = None             # match one deal vs buyers
    buyer_id: Optional[int] = None            # match one buyer vs deals
    limit: int = 20
    min_score: float = 0.25                   # 0..1
    # Optional ad-hoc deal payload (used if deal_id not provided)
    deal: Optional[DealBriefIn] = None

class MatchHit(BaseModel):
    buyer_id: int
    buyer_name: str
    score: float
    reasons: List[str]

class DealHit(BaseModel):
    deal_id: int
    headline: str
    score: float
    reasons: List[str]

class MatchComputeOut(BaseModel):
    mode: str
    total: int
    hits: List[MatchHit] | List[DealHit]
