from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.property_to_lead_orchestrator import (
    run_property_to_lead_conversion,
)

router = APIRouter(
    prefix="/heimdall/property-to-lead",
    tags=["Heimdall Property To Lead"],
)


class PropertyToLeadRequest(BaseModel):
    property_intel_id: str
    created_by: str = "heimdall"


@router.post("/convert")
def convert_property_to_lead(
    payload: PropertyToLeadRequest,
    db: Session = Depends(get_db),
):
    """
    Convert researched property into real lead and create deal record.
    
    Input: property_intel_id from drive-for-dollars workflow
    
    Prerequisites:
    - Property must be in READY_FOR_OUTREACH, RESEARCH_UPDATED, or CONVERTED_TO_LEAD status
    - outreach_allowed must be true
    - (Typically) Owner has responded positively to outreach letter
    
    Workflow:
    1. Load property intel record
    2. Validate readiness gates
    3. Convert to lead payload (owner name, address, contact)
    4. Create deal record with source=property_intel
    5. Mark property as converted_to_lead
    
    Output:
    - status: PROPERTY_CONVERTED_TO_LEAD | BLOCKED | ERROR
    - deal_id: New deal record ID for further underwriting
    - lead_payload: Owner info + contact details
    
    Next steps:
    1. Collect seller response details (yes/maybe/no)
    2. Fill underwriting fields (loan amount, timeline, etc.)
    3. Run POST /heimdall/intake-db/deal for full Heimdall evaluation
    """
    return run_property_to_lead_conversion(
        db=db,
        property_intel_id=payload.property_intel_id,
        created_by=payload.created_by,
    )
