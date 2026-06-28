from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.heimdall.education.buyer_sourcing_engine import (
    generate_buyer_sourcing_plan,
    rank_buyers_for_deal,
    draft_buyer_message,
)

router = APIRouter(prefix="/heimdall/buyer-sourcing", tags=["Heimdall Buyer Sourcing"])


class BuyerSourcingPlanRequest(BaseModel):
    city: str
    strategy: str


class BuyerProfile(BaseModel):
    id: str
    name: str
    target_cities: List[str]
    property_types: List[str]
    min_price: float
    max_price: float
    rehab_tolerance: List[str]
    proof_of_funds_verified: bool = False
    close_speed_days: int = 30


class DealBuyerMatchRequest(BaseModel):
    id: str
    property_address: str
    city: str
    property_type: str
    arv: float
    target_buyer_price: float
    estimated_repairs: float
    rehab_level: str
    required_close_days: int = 30
    buyers: List[BuyerProfile]


class DraftBuyerMessageRequest(BaseModel):
    deal: Dict[str, Any]
    buyer: Dict[str, Any]


@router.post("/plan")
def buyer_sourcing_plan(payload: BuyerSourcingPlanRequest):
    """
    Generate buyer sourcing plan for a city/strategy.
    
    Returns:
    - local_sources: City-specific buyer sources (meetups, groups, networks)
    - generic_sources_to_search: General search lane categories
    - instructions: Compliance and best-practice guidelines
    """
    return generate_buyer_sourcing_plan(payload.city, payload.strategy)


@router.post("/match")
def buyer_match(payload: DealBuyerMatchRequest):
    """
    Rank buyers against a specific deal using buy-box matching.
    
    Returns:
    - ranked_buyers: All buyers scored and sorted (highest to lowest)
    - recommended_send_list: Buyers with match_score >= 60 (ready to reach out)
    - blocked_buyers: Buyers with match_score < 40 (do not send)
    - human_approval_required_before_message: Always true
    """
    deal = payload.model_dump()
    buyers = deal.pop("buyers")
    return rank_buyers_for_deal(deal, buyers)


@router.post("/draft-message")
def buyer_message(payload: DraftBuyerMessageRequest):
    """
    Draft an initial buyer outreach message for approval.
    
    Returns:
    - message: Auto-drafted interest-check message
    - requires_approval_before_sending: Always true
    
    Human must review and approve before sending.
    """
    return draft_buyer_message(payload.deal, payload.buyer)
