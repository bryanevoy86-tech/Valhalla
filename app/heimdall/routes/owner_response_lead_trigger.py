from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.owner_response_lead_trigger import (
    trigger_lead_conversion_from_owner_response,
)

router = APIRouter(
    prefix="/heimdall/owner-response-lead",
    tags=["Heimdall Owner Response Lead Trigger"],
)


class OwnerResponseLeadTriggerRequest(BaseModel):
    property_intel_id: str
    triggered_by: str = "heimdall"


@router.post("/trigger")
def trigger_owner_response_lead(
    payload: OwnerResponseLeadTriggerRequest,
    db: Session = Depends(get_db),
):
    """
    Trigger lead conversion after positive owner response.
    
    Input: property_intel_id from POST /owner-response/intake
    
    Prerequisites:
    - Property status must be OWNER_INTERESTED or OWNER_MAYBE
    - outreach_allowed must be true
    - Status must NOT be in BLOCKED_STATUSES (DO_NOT_CONTACT, VERIFY_OWNER_DATA, etc.)
    
    Workflow:
    1. Load property intel record
    2. Validate response allows conversion
    3. Call property-to-lead conversion
    4. Create deal record with source=property_intel
    5. Return deal_id for full Heimdall intake
    
    Allowed conversions:
    - OWNER_INTERESTED → Immediate lead conversion + call task creation
    - OWNER_MAYBE → Immediate lead conversion + follow-up task
    
    Blocked conversions:
    - DO_NOT_CONTACT → Never convert (permanent block)
    - VERIFY_OWNER_DATA → Manual verification required first
    - OWNER_RESPONSE_MANUAL_REVIEW → Manual review required first
    
    Output:
    - status: LEAD_CONVERSION_TRIGGERED | BLOCKED | NOT_READY | ERROR
    - conversion_result: Contains deal_id if conversion succeeded
    
    Next step:
    - Fill deal underwriting fields
    - Run POST /heimdall/intake-db/deal for full evaluation
    """
    return trigger_lead_conversion_from_owner_response(
        db=db,
        property_intel_id=payload.property_intel_id,
        triggered_by=payload.triggered_by,
    )
