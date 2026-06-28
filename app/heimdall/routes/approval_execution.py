from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.approval_execution_service import execute_approval_decision

router = APIRouter(prefix="/heimdall/approvals", tags=["Heimdall Approval Execution"])


class ApprovalExecutionRequest(BaseModel):
    status: str
    reviewed_by: str
    notes: str = ""


@router.post("/{approval_id}/execute")
def execute_approval(
    approval_id: str,
    payload: ApprovalExecutionRequest,
    db: Session = Depends(get_db),
):
    """
    Execute an approval decision (APPROVED or REJECTED).
    
    Updates approval record and linked deal record with:
    - Decision status and timestamp
    - Reviewer name and notes
    - Approval history entry
    - Next allowed action based on approval type
    
    Approval types and unlock rules:
    - heimdall_command: APPROVED → continue_pipeline, REJECTED → move_to_pass_or_nurture
    - seller_message: APPROVED → send_allowed=true, REJECTED → revise
    - buyer_outreach: APPROVED → send_allowed=true, REJECTED → remove from queue
    - lawyer_packet: APPROVED → send_allowed=true, REJECTED → revise
    - contract_terms: APPROVED → contract_allowed=true, REJECTED → blocked
    
    Returns:
    - approval_id, approval_type, decision (APPROVED/REJECTED)
    - next_action: What can happen next
    - send_allowed: Whether messages can now be sent
    - contract_allowed: Whether contract can proceed
    - deal_update: Deal state changes (if any)
    """
    return execute_approval_decision(
        db=db,
        approval_id=approval_id,
        status=payload.status,
        reviewed_by=payload.reviewed_by,
        notes=payload.notes,
    )
