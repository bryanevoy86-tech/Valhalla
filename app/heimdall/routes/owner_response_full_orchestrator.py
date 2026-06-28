from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.owner_response_full_orchestrator import (
    run_owner_response_full_orchestrator,
)

router = APIRouter(
    prefix="/heimdall/owner-response-full",
    tags=["Heimdall Owner Response Full Orchestrator"],
)


class OwnerResponseFullRequest(BaseModel):
    property_intel_id: str
    response_text: str
    response_channel: str = "unknown"
    received_by: str = "heimdall"
    auto_trigger_lead_conversion: bool = True


@router.post("/run")
def run_owner_response_full(
    payload: OwnerResponseFullRequest,
    db: Session = Depends(get_db),
):
    """
    Full owner response orchestration in one call.
    
    Input: Owner response from email, SMS, call notes, form submission, etc.
    
    Workflow (automated):
    1. Classify response (yes, maybe, no, stop, wrong contact, unclear)
    2. Update property intel status
    3. Create follow-up tasks as needed
    4. If auto_trigger_lead_conversion=true:
       → Check if conversion is safe
       → Convert to lead + create deal record if status allows
       → Skip conversion if DO_NOT_CONTACT, VERIFY_OWNER_DATA, or UNCLEAR
    5. Return combined results with next actions
    
    Response processing:
    - "yes, interested, call me" → OWNER_INTERESTED + CRITICAL call task + auto-convert to lead
    - "maybe, depends, how much" → OWNER_MAYBE + HIGH follow-up task + auto-convert to lead
    - "no, not interested" → NURTURE_OR_CLOSE + no conversion
    - "stop, do not contact" → DO_NOT_CONTACT + block conversion + block outreach
    - "wrong person, not mine" → VERIFY_OWNER_DATA + HIGH verification task + block conversion
    - [unclear] → OWNER_RESPONSE_MANUAL_REVIEW + MEDIUM review task + block conversion
    
    Output:
    - status: OWNER_RESPONSE_ORCHESTRATED | ERROR
    - response_result: Classification + property status + tasks created
    - conversion_result: Deal created (if auto_trigger=true and status allows)
    - human_review_required: true if response needs manual review
    - next_action: Next step based on classification
    
    Set auto_trigger_lead_conversion=false to process response without auto-conversion.
    """
    return run_owner_response_full_orchestrator(
        db=db,
        property_intel_id=payload.property_intel_id,
        response_text=payload.response_text,
        response_channel=payload.response_channel,
        received_by=payload.received_by,
        auto_trigger_lead_conversion=payload.auto_trigger_lead_conversion,
    )
