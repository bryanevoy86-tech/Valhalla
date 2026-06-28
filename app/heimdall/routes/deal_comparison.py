from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

from app.heimdall.education.deal_comparison_engine import compare_deals

router = APIRouter(
    prefix="/heimdall/deal-comparison",
    tags=["Heimdall Deal Comparison"],
)


class DealComparisonRequest(BaseModel):
    deals: List[Dict[str, Any]]


@router.post("/compare")
def compare(payload: DealComparisonRequest):
    """
    Compare multiple deals and rank by priority.
    
    Input: Array of deal objects with evaluation data
    
    Each deal should contain:
    - id: deal ID
    - property_address: street address
    - deal_score: 0-100 (underwriting viability)
    - motivation_score: 0-100 (seller urgency)
    - buyer_demand_score: 0-100 (cash buyer interest)
    - market_score: 0-100 (market conditions)
    - projected_spread: $ amount (profit potential)
    - red_flags: array (title issues, structural problems, etc.)
    - missing_data: array (what's not yet researched)
    - legal_review_required: bool
    - lawyer_review_complete: bool
    - seller_authority_verified: bool
    - buyer_demand_verified: bool
    
    Output: Ranked deals with priority scores + recommendation
    
    Priority bands:
    - TOP_PRIORITY (85+): Focus all effort here
    - HIGH_PRIORITY (70-84): Strong opportunity
    - MEDIUM_PRIORITY (55-69): Viable if data improved
    - LOW_PRIORITY (40-54): Only if nothing else available
    - DO_NOT_PRIORITIZE (<40): Skip, keep sourcing
    
    Use case:
    - Every week: Pull all active deals from dashboard
    - POST /compare with all deal data
    - Get ranked list with top 3 to focus on
    - Ignore bottom tier (DO_NOT_PRIORITIZE)
    """
    return compare_deals(payload.deals)
