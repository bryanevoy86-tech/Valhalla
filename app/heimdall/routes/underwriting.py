from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.heimdall.education.underwriting_engine import underwrite_deal

router = APIRouter(prefix="/heimdall/underwriting", tags=["Heimdall Underwriting"])


class DealUnderwriteRequest(BaseModel):
    strategy: str
    arv: float
    purchase_price: float
    repairs: float
    assignment_fee: Optional[float] = 15000
    safety_buffer: Optional[float] = 10000
    buyer_price: Optional[float] = None

    seller_authority_verified: bool = False
    arv_supported: bool = False
    repair_confidence: str = "low"
    buyer_demand_verified: bool = False
    legal_review_required: bool = True
    lawyer_review_complete: bool = False

    numbers_best_case_only: bool = False
    title_issue_known: bool = False

    seller_motivation_score: int = 0
    spread_margin_score: int = 0
    arv_confidence_score: int = 0
    repair_confidence_score: int = 0
    buyer_demand_score: int = 0
    legal_clarity_score: int = 0
    market_strength_score: int = 0


@router.post("/deal")
def heimdall_underwrite_deal(payload: DealUnderwriteRequest):
    """
    Underwrite a deal using Heimdall's education layer and underwriting engine.
    
    Returns:
    - recommendation: PASS_OR_HOLD, HOLD, RENEGOTIATE_OR_PASS, STRONG_CANDIDATE_PENDING_APPROVAL, POSSIBLE_CANDIDATE_MORE_DUE_DILIGENCE
    - reason: Explanation of recommendation
    - mao: Maximum Allowable Offer
    - deal_score: 0-100 score based on education weights
    - red_flags: List of detected red flags
    - missing_data: List of required data that's missing
    - human_approval_required: Always true (Heimdall recommends, humans approve)
    """
    return underwrite_deal(payload.model_dump())
