from typing import Any, Dict
from sqlalchemy.orm import Session

from app.heimdall.education.owner_outreach_letter_engine import generate_owner_outreach_packet
from app.heimdall.services.persistence_service import create_approval, create_message


def create_owner_outreach_approval(
    db: Session,
    property_record: Dict[str, Any],
    created_by: str = "heimdall",
) -> Dict[str, Any]:
    """
    Create owner outreach approval item from property intel record.
    
    This creates:
    1. Approval record (PENDING status)
    2. Message record (DRAFT_PENDING_APPROVAL status)
    
    Both are gated: neither can proceed until approval is granted.
    
    Returns:
    - approval_id: For tracking approval decision
    - message_id: For gating message sends
    - packet: Complete outreach packet with draft letter
    - send_blocked_until_approved: true
    """
    packet = generate_owner_outreach_packet(property_record)

    if not packet.get("allowed"):
        return {
            "status": "BLOCKED",
            "reason": packet.get("reason"),
            "packet": packet,
        }

    approval = create_approval(db, {
        "deal_id": property_record.get("source_property_intel_id") or property_record.get("id"),
        "approval_type": "owner_outreach_letter",
        "status": "PENDING",
        "title": "Approve owner outreach letter",
        "created_by": created_by,
        "payload": packet,
    })

    message = create_message(db, {
        "deal_id": property_record.get("source_property_intel_id") or property_record.get("id"),
        "recipient_type": "owner",
        "recipient_name": packet.get("owner_name"),
        "status": "DRAFT_PENDING_APPROVAL",
        "message_type": "owner_outreach_letter",
        "payload": packet,
        "body": packet.get("draft_letter"),
    })

    return {
        "status": "OWNER_OUTREACH_APPROVAL_CREATED",
        "approval_id": approval.id,
        "message_id": message.id,
        "packet": packet,
        "send_blocked_until_approved": True,
    }
