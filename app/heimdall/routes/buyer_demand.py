from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.heimdall.education.buyer_demand_engine import evaluate_buyer_demand

router = APIRouter(prefix="/heimdall/buyers", tags=["Heimdall Buyer Demand"])


class BuyerDemandRequest(BaseModel):
    property_address: str
    city: str
    strategy: str

    arv: float
    contract_price: float
    estimated_repairs: float
    target_buyer_price: float

    verified_cash_buyers_count: int
    recent_investor_sales_count: int
    buyer_feedback_score: int
    days_to_close_expectation: int

    major_rehab_required: bool = False
    rehab_buyer_confirmed: bool = False
    rural_or_low_liquidity_area: bool = False


@router.post("/demand-score")
def buyer_demand_score(payload: BuyerDemandRequest):
    """
    Score buyer demand and disposition viability for a deal.
    
    Returns:
    - buyer_demand_score: 0-100 score based on buyer pool, activity, feedback, spread, close speed
    - recommendation: STRONG/MODERATE/WEAK_DISPOSITION_CONFIDENCE or DO_NOT_CONTRACT_YET or HOLD_MISSING_DATA
    - red_flags: Disposition blockers (thin buyer pool, no spread, no rehab buyer, etc.)
    - missing_data: Required data that's missing
    - next_action: Suggested next step
    - human_approval_required: Always true
    """
    return evaluate_buyer_demand(payload.model_dump())
