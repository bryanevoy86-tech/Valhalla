from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.heimdall.education.lead_motivation_engine import score_lead_motivation

router = APIRouter(prefix="/heimdall/leads", tags=["Heimdall Lead Motivation"])


class LeadMotivationRequest(BaseModel):
    seller_name: str
    property_address: str
    reason_for_selling: str
    timeline_to_sell: str
    asking_price: float
    property_condition: str
    mortgage_or_debt_issue: bool = False
    vacant_or_occupied: str
    seller_responsiveness: str

    estimated_arv: Optional[float] = None
    seller_authority_verified: bool = False
    wants_retail_price: bool = False
    refuses_basic_questions: bool = False
    price_flexible: bool = False


@router.post("/motivation-score")
def lead_motivation_score(payload: LeadMotivationRequest):
    """
    Score a seller lead for motivation and urgency.
    
    Returns:
    - motivation_score: 0-100 score based on urgency, motivation, condition, responsiveness
    - lead_lane: HOT_LEAD_CALL_NOW, WARM_LEAD_FOLLOW_UP_FAST, NURTURE_SEQUENCE, LOW_PRIORITY_OR_DISQUALIFY
    - recommended_next_action: Suggested follow-up action
    - red_flags: Motivation-blocking red flags
    - missing_data: Required data that's missing
    - human_approval_required: Always false (this is auto-routing, humans decide follow-up)
    """
    return score_lead_motivation(payload.model_dump())
