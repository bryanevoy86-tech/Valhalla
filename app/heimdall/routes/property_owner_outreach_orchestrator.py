from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.property_owner_outreach_orchestrator import (
    run_property_owner_outreach_orchestrator,
)

router = APIRouter(
    prefix="/heimdall/property-owner-outreach",
    tags=["Heimdall Property Owner Outreach"],
)


class PropertyOwnerOutreachRequest(BaseModel):
    property_intel_id: str
    created_by: str = "heimdall"


@router.post("/run")
def run_owner_outreach(
    payload: PropertyOwnerOutreachRequest,
    db: Session = Depends(get_db),
):
    """
    Run full Property Intel → Owner Outreach orchestration.
    
    Input: property_intel_id from POST /heimdall/property-intel-db/records
    
    Workflow:
    1. Load property intel record
    2. Check readiness: ownership_verified? distress ≥50? outreach_allowed?
    3. If blocked: return OUTREACH_BLOCKED with reasons
    4. If ready:
       - Generate owner letter (distress-tailored)
       - Create PENDING approval
       - Create DRAFT_PENDING_APPROVAL message
       - Return approval_id, message_id, draft_letter
    
    Output:
    - status: OWNER_OUTREACH_READY_FOR_APPROVAL | OUTREACH_BLOCKED | ERROR
    - property: Full property intel record
    - approval_result: approval_id, message_id, draft_letter, safe_language_rules
    
    Next steps:
    1. Review draft_letter
    2. POST /heimdall/approvals/{approval_id}/execute to approve
    3. POST /heimdall/messages/{message_id}/send-gate/mark-ready
    4. Send message
    """
    return run_property_owner_outreach_orchestrator(
        db=db,
        property_intel_id=payload.property_intel_id,
        created_by=payload.created_by,
    )
