from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.owner_response_service import intake_owner_response

router = APIRouter(
    prefix="/heimdall/owner-response",
    tags=["Heimdall Owner Response"],
)


class OwnerResponseRequest(BaseModel):
    property_intel_id: str
    response_text: str
    response_channel: str = "unknown"
    received_by: str = "heimdall"


@router.post("/intake")
def owner_response_intake(
    payload: OwnerResponseRequest,
    db: Session = Depends(get_db),
):
    """
    Intake owner response and update property/lead status.
    
    Input: Response from owner (email, call notes, form submission, etc.)
    
    Response types and automatic actions:
    - "yes, interested, call me" → OWNER_INTERESTED + create CRITICAL call task
    - "maybe, depends, how much" → OWNER_MAYBE + create HIGH follow-up task
    - "no, not interested" → NURTURE_OR_CLOSE (cold lead)
    - "stop, do not contact" → DO_NOT_CONTACT + block all future outreach
    - "wrong person, not mine" → VERIFY_OWNER_DATA + create HIGH verification task
    - [unclear response] → OWNER_RESPONSE_MANUAL_REVIEW + create MEDIUM review task
    
    Output:
    - status: OWNER_RESPONSE_PROCESSED | ERROR
    - property_status: Updated research_status
    - classification: Response classification with priority and next_action
    - human_review_required: true if response needs manual review
    
    Flow:
    1. Classify response text into category
    2. Update property record status
    3. Create follow-up tasks (call, verify, review, etc.)
    4. Log response in audit trail (notes array)
    5. Return classification and next actions
    """
    return intake_owner_response(
        db=db,
        property_intel_id=payload.property_intel_id,
        response_text=payload.response_text,
        response_channel=payload.response_channel,
        received_by=payload.received_by,
    )
