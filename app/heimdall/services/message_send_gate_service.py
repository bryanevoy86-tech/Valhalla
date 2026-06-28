from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.heimdall.models.persistence import HeimdallMessage, HeimdallApproval


def find_matching_approval(
    db: Session,
    deal_id: str,
    approval_type: str,
    recipient_id: Optional[str] = None,
) -> Optional[HeimdallApproval]:
    """
    Find an approved approval record matching the given criteria.
    
    Searches for APPROVED approvals of the specified type.
    If recipient_id provided, also matches on buyer_id or recipient_id in payload.
    """
    approvals = (
        db.query(HeimdallApproval)
        .filter(HeimdallApproval.deal_id == deal_id)
        .filter(HeimdallApproval.status == "APPROVED")
        .all()
    )

    for approval in approvals:
        data = approval.data or {}

        if data.get("approval_type") != approval_type:
            continue

        payload = data.get("payload", {}) or {}

        if recipient_id:
            if payload.get("buyer_id") == recipient_id or payload.get("recipient_id") == recipient_id:
                return approval
        else:
            return approval

    return None


def get_required_approval_type(recipient_type: str) -> Optional[str]:
    """
    Map recipient type to required approval type.
    
    - seller → seller_message
    - buyer → buyer_outreach
    - lawyer → lawyer_packet
    - owner → owner_outreach_letter
    """
    if recipient_type == "seller":
        return "seller_message"

    if recipient_type == "buyer":
        return "buyer_outreach"

    if recipient_type == "lawyer":
        return "lawyer_packet"

    if recipient_type == "owner":
        return "owner_outreach_letter"

    return None


def check_message_send_gate(db: Session, message_id: str) -> Dict[str, Any]:
    """
    Check if message is approved and ready to send.
    
    Validates that a matching APPROVED approval exists for the message's recipient type.
    Works for all recipient types: seller, buyer, lawyer, owner.
    
    Returns send_allowed flag and approval_id if approved.
    """
    message = db.query(HeimdallMessage).filter(HeimdallMessage.id == message_id).first()

    if not message:
        return {
            "send_allowed": False,
            "reason": "Message not found.",
        }

    data = message.data or {}
    deal_id = message.deal_id or data.get("deal_id")
    recipient_type = message.recipient_type or data.get("recipient_type")
    recipient_id = data.get("recipient_id")

    approval_type = get_required_approval_type(recipient_type)

    if not approval_type:
        return {
            "send_allowed": False,
            "reason": "Unknown recipient type. Manual review required.",
            "message_id": message_id,
            "recipient_type": recipient_type,
        }

    approval = find_matching_approval(
        db=db,
        deal_id=deal_id,
        approval_type=approval_type,
        recipient_id=recipient_id,
    )

    if not approval:
        return {
            "send_allowed": False,
            "reason": f"No approved {approval_type} approval found.",
            "message_id": message_id,
            "deal_id": deal_id,
            "recipient_type": recipient_type,
        }

    return {
        "send_allowed": True,
        "reason": "Matching approval found.",
        "message_id": message_id,
        "deal_id": deal_id,
        "recipient_type": recipient_type,
        "approval_id": approval.id,
        "status_to_apply": "READY_TO_SEND",
    }


def mark_message_ready_to_send(db: Session, message_id: str) -> Dict[str, Any]:
    """
    Update message status to READY_TO_SEND if gate check passes.
    
    Calls check_message_send_gate to verify approval exists.
    If approved: sets message status=READY_TO_SEND, saves approval_id in data.
    If blocked: returns gate check result with reason.
    """
    gate = check_message_send_gate(db, message_id)

    if not gate.get("send_allowed"):
        return gate

    message = db.query(HeimdallMessage).filter(HeimdallMessage.id == message_id).first()

    message.status = "READY_TO_SEND"
    message.data = {
        **(message.data or {}),
        "send_gate_passed": True,
        "approval_id": gate.get("approval_id"),
    }

    db.commit()
    db.refresh(message)

    return {
        **gate,
        "message_status": message.status,
    }
