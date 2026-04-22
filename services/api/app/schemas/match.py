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
    disposition_status: Optional[str] = None
    disposition_notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class DealDispositionIn(BaseModel):
    disposition_status: str = Field(..., description="Disposition status: new, buyer_review, offer_out, assigned, closed, dead")
    disposition_notes: Optional[str] = Field(None, description="Optional notes about the disposition")

class DealActionIn(BaseModel):
    action: str = Field(..., description="Action to perform: analyze, hot, dead, pipeline")

class DealAnalysis(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Analysis score 0-100")
    risk: str = Field(..., description="Risk level: low, medium, high")
    strategy: str = Field(..., description="Strategy: flip, brrrr, wholesale, hold, unknown")
    recommendation: str = Field(..., description="Short recommendation text")

class DealAnalysisResponse(BaseModel):
    deal_id: int
    headline: str
    analysis: DealAnalysis

class ApplyRecommendationResponse(BaseModel):
    deal_id: int
    headline: str
    next_step: str = Field(..., description="Next step: pipeline, review, dead, needs_more_data")
    status_applied: Optional[str] = Field(None, description="Status that was applied (pipeline or dead), or null")
    message: str = Field(..., description="Short explanation of the recommendation")

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

class AutomationRuleResponse(BaseModel):
    deal_id: int
    headline: str
    status: str
    disposition_status: Optional[str] = None
    action_taken: str = Field(..., description="initialized_disposition | awaiting_buyer_review | no_action_dead_deal | moved_to_pipeline | no_action")
    message: str
    model_config = ConfigDict(from_attributes=True)
