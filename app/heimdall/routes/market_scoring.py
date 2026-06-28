from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.heimdall.education.market_scoring_engine import evaluate_market

router = APIRouter(prefix="/heimdall/markets", tags=["Heimdall Market Scoring"])


class MarketScoreRequest(BaseModel):
    city: str
    province_or_state: str
    country: str

    population: float
    median_income: float
    average_rent: float
    vacancy_rate: float
    median_home_price: float

    investor_activity_score: int
    buyer_pool_score: int
    distressed_inventory_score: int
    landlord_tenant_risk_score: int
    economic_stability_score: int


@router.post("/score")
def score_market(payload: MarketScoreRequest):
    """
    Score a market for expansion viability.
    
    Returns:
    - final_decision: APPROVED_FOR_TEST_ZONE or HOLD_OR_RESEARCH_MORE
    - market_score: 0-100 score
    - recommendation: STRONG_MARKET_CANDIDATE, TEST_MARKET_WITH_LIMITED_BUDGET, WATCHLIST_ONLY, DO_NOT_ENTER_YET
    - rent_to_price_ratio: Annual rent / home price ratio
    - expansion_blockers: List of barriers to entry
    - missing_data: Required data that's missing
    - warnings: Market-specific cautions
    - human_approval_required: Always true
    """
    return evaluate_market(payload.model_dump())
