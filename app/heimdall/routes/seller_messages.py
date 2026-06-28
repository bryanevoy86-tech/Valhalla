from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from app.heimdall.education.seller_message_engine import draft_seller_message

router = APIRouter(prefix="/heimdall/messages", tags=["Heimdall Seller Messages"])


class SellerMessageDraftRequest(BaseModel):
    deal: Dict[str, Any]
    command_result: Dict[str, Any]


@router.post("/seller/draft")
def draft_seller(payload: SellerMessageDraftRequest):
    """
    Draft a seller outreach message based on deal status and Heimdall command.
    
    Message types auto-determined:
    - soft_offer_or_next_step: When underwriting score is strong (STRONG_CANDIDATE)
    - renegotiation: When price exceeds MAO (RENEGOTIATE)
    - missing_information_request: When data is incomplete (HOLD_MISSING_INFORMATION)
    - due_diligence_followup: When deal is borderline (POSSIBLE_DEAL_MORE_DUE_DILIGENCE)
    - nurture_or_polite_hold: When deal doesn't fit now (PASS_OR_HOLD)
    - general_followup: Default follow-up message
    
    Returns:
    - draft_message: Tonally appropriate message ready for review
    - requires_human_approval_before_sending: Always true
    - legal_warning: Reminder not to send binding language without approval
    """
    return draft_seller_message(payload.deal, payload.command_result)
