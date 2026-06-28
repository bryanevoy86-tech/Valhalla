from typing import Any, Dict
from sqlalchemy.orm import Session

from app.heimdall.education.owner_outreach_letter_engine import generate_owner_outreach_packet
from app.heimdall.services.owner_outreach_approval_service import (
    create_owner_outreach_approval,
)
from app.heimdall.services.message_send_gate_service import mark_message_ready_to_send


def orchestrate_property_to_owner_outreach(
    db: Session,
    property_record: Dict[str, Any],
    created_by: str = "heimdall",
) -> Dict[str, Any]:
    """
    Full orchestration: Property Intel → Owner Outreach Letter → Approval → Send Gate.
    
    One-shot endpoint to:
    1. Validate property meets outreach criteria (distress, ownership verified, etc.)
    2. Generate owner letter (tailored to distress level)
    3. Create approval record (PENDING)
    4. Create message record (DRAFT_PENDING_APPROVAL)
    5. Return complete packet with approval_id and message_id
    
    The approval and message are gated:
    - Approval must be APPROVED before anything sends
    - Message status must be updated via approval execution
    - Send gate validates approval exists before allowing send
    
    Example workflow:
    1. POST /heimdall/owner-outreach-orchestrator with property_record
    2. Get back: approval_id, message_id, draft_letter
    3. User reviews and approves via POST /heimdall/approvals/{approval_id}/execute
    4. System updates message status to READY_TO_SEND
    5. Check send gate: GET /heimdall/messages/{message_id}/send-gate
    6. If approved, message can be sent
    """
    
    # Step 1: Validate outreach packet generation
    packet = generate_owner_outreach_packet(property_record)
    
    if not packet.get("allowed"):
        return {
            "status": "OUTREACH_BLOCKED",
            "reason": packet.get("reason"),
            "distress_score": packet.get("distress_score"),
            "packet": packet,
        }
    
    # Step 2: Create approval + message via approval service
    approval_result = create_owner_outreach_approval(
        db=db,
        property_record=property_record,
        created_by=created_by,
    )
    
    if approval_result.get("status") != "OWNER_OUTREACH_APPROVAL_CREATED":
        return approval_result
    
    # Step 3: Return complete orchestration result
    return {
        "status": "OUTREACH_ORCHESTRATION_COMPLETE",
        "approval_id": approval_result.get("approval_id"),
        "message_id": approval_result.get("message_id"),
        "packet": approval_result.get("packet"),
        "next_steps": [
            "1. Review draft_letter in packet",
            "2. POST /heimdall/approvals/{approval_id}/execute with APPROVED status",
            "3. System updates message status to READY_TO_SEND",
            "4. GET /heimdall/messages/{message_id}/send-gate to verify approval",
            "5. Send message via integration (email/mail/SMS)",
        ],
        "workflow": {
            "property_intel_id": property_record.get("id"),
            "approval_pending": True,
            "message_draft_pending_approval": True,
            "send_blocked_until_approved": True,
        },
    }
