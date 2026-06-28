from typing import Any, Dict, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.heimdall.services.persistence_service import (
    update_approval,
    get_deal,
    update_deal,
)


APPROVAL_NEXT_ACTIONS = {
    "heimdall_command": {
        "APPROVED": "continue_pipeline",
        "REJECTED": "move_to_pass_or_nurture",
    },
    "seller_message": {
        "APPROVED": "seller_message_unlocked_for_sending",
        "REJECTED": "revise_seller_message",
    },
    "buyer_outreach": {
        "APPROVED": "buyer_message_unlocked_for_sending",
        "REJECTED": "remove_buyer_from_send_queue",
    },
    "lawyer_packet": {
        "APPROVED": "lawyer_packet_unlocked_for_sending",
        "REJECTED": "revise_lawyer_packet",
    },
    "contract_terms": {
        "APPROVED": "contract_can_move_to_lawyer_or_signature_stage",
        "REJECTED": "contract_blocked",
    },
}


def execute_approval_decision(
    db: Session,
    approval_id: str,
    status: str,
    reviewed_by: str,
    notes: str = "",
) -> Dict[str, Any]:
    normalized_status = status.upper().strip()

    if normalized_status not in ["APPROVED", "REJECTED"]:
        return {
            "status": "ERROR",
            "message": "Approval status must be APPROVED or REJECTED.",
        }

    approval = update_approval(
        db=db,
        approval_id=approval_id,
        status=normalized_status,
        reviewed_by=reviewed_by,
        notes=notes,
    )

    if not approval:
        return {
            "status": "ERROR",
            "message": "Approval record not found.",
        }

    approval_data = approval.data or {}
    approval_type = approval_data.get("approval_type") or approval.approval_type
    deal_id = approval_data.get("deal_id") or approval.deal_id

    next_action = APPROVAL_NEXT_ACTIONS.get(
        approval_type,
        {},
    ).get(normalized_status, "manual_review_required")

    deal_update_result: Optional[Dict[str, Any]] = None

    if deal_id:
        deal = get_deal(db, deal_id)

        if deal:
            deal_data = deal.data or {}
            approval_history = deal_data.get("approval_history", [])

            approval_history.append({
                "approval_id": approval_id,
                "approval_type": approval_type,
                "status": normalized_status,
                "reviewed_by": reviewed_by,
                "notes": notes,
                "timestamp": datetime.utcnow().isoformat(),
                "next_action": next_action,
            })

            updates = {
                "approval_history": approval_history,
                "last_approval_status": normalized_status,
                "last_approval_type": approval_type,
                "last_approval_next_action": next_action,
            }

            if approval_type == "heimdall_command" and normalized_status == "REJECTED":
                updates["state"] = "PASS"
                updates["manual_override_reason"] = notes or "Heimdall command rejected."

            if approval_type == "lawyer_packet" and normalized_status == "APPROVED":
                updates["lawyer_packet_approved"] = True

            if approval_type == "seller_message" and normalized_status == "APPROVED":
                updates["seller_message_approved"] = True

            if approval_type == "buyer_outreach" and normalized_status == "APPROVED":
                updates["buyer_outreach_approved"] = True

            updated_deal = update_deal(db, deal_id, updates)

            if updated_deal:
                deal_update_result = {
                    "deal_id": updated_deal.id,
                    "state": updated_deal.state,
                    "updated": True,
                }

    return {
        "status": "APPROVAL_EXECUTED",
        "approval_id": approval_id,
        "approval_type": approval_type,
        "decision": normalized_status,
        "reviewed_by": reviewed_by,
        "next_action": next_action,
        "deal_update": deal_update_result,
        "send_allowed": next_action in [
            "seller_message_unlocked_for_sending",
            "buyer_message_unlocked_for_sending",
            "lawyer_packet_unlocked_for_sending",
        ],
        "contract_allowed": next_action == "contract_can_move_to_lawyer_or_signature_stage",
    }
