from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.message_send_gate_service import check_message_send_gate, mark_message_ready_to_send

router = APIRouter(prefix="/heimdall/messages", tags=["Heimdall Message Send Gate"])


@router.get("/{message_id}/send-gate")
def check_send_gate(
    message_id: str,
    db: Session = Depends(get_db),
):
    """
    Check if a message is approved and ready to send.
    
    Gate logic by recipient type:
    - seller: requires APPROVED seller_message approval
    - buyer: requires APPROVED buyer_outreach approval
    - lawyer: requires APPROVED lawyer_packet approval
    - owner: requires APPROVED owner_outreach_letter approval
    
    Returns:
    - send_allowed: true/false
    - approval_id: if approved (for tracking)
    - reason: detailed status message
    """
    return check_message_send_gate(db, message_id)


@router.post("/{message_id}/send-gate/mark-ready")
def mark_ready(
    message_id: str,
    db: Session = Depends(get_db),
):
    """
    Update message status to READY_TO_SEND if approval gate passes.
    
    This is called after approval is granted:
    1. POST /heimdall/approvals/{approval_id}/execute (approval APPROVED)
    2. System routes to this: POST /heimdall/messages/{message_id}/send-gate/mark-ready
    3. Check gate passes, message status → READY_TO_SEND
    4. Message can now be sent
    """
    return mark_message_ready_to_send(db, message_id)
