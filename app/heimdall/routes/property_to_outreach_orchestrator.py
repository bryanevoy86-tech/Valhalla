from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.property_to_outreach_orchestrator_service import (
    orchestrate_property_to_owner_outreach,
)

router = APIRouter(
    prefix="/heimdall/owner-outreach-orchestrator",
    tags=["Heimdall Owner Outreach Orchestrator"],
)


class PropertyToOutreachRequest(BaseModel):
    property_record: Dict[str, Any]
    created_by: str = "heimdall"


@router.post("/execute")
def execute_orchestration(payload: PropertyToOutreachRequest, db: Session = Depends(get_db)):
    """
    Full Property Intel → Owner Outreach orchestration in one call.
    
    Validates property meets outreach criteria, generates letter,
    creates approval, creates message draft, and blocks sending.
    
    Input:
    - property_record: Complete property intel record with distress_analysis
    - created_by: User/system creating the approval
    
    Output:
    - approval_id: ID for approval decision
    - message_id: ID for message sending
    - draft_letter: Complete owner letter (distress-tailored)
    - next_steps: Workflow instructions
    
    Workflow:
    1. This endpoint creates PENDING approval + DRAFT_PENDING_APPROVAL message
    2. User approves: POST /heimdall/approvals/{approval_id}/execute
    3. System updates message to READY_TO_SEND
    4. Check gate: GET /heimdall/messages/{message_id}/send-gate
    5. Send message (future integration)
    """
    return orchestrate_property_to_owner_outreach(
        db=db,
        property_record=payload.property_record,
        created_by=payload.created_by,
    )
