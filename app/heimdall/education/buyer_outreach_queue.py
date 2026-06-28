from typing import Any, Dict, List
from datetime import datetime

from app.heimdall.education.buyer_sourcing_engine import draft_buyer_message


def build_buyer_outreach_queue(
    deal: Dict[str, Any],
    matched_buyers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    queue_items = []

    for buyer in matched_buyers:
        match_score = buyer.get("match_score", 0)

        if match_score < 60:
            continue

        draft = draft_buyer_message(deal, buyer)

        queue_items.append({
            "queue_id": f"buyer_outreach_{deal.get('id')}_{buyer.get('buyer_id') or buyer.get('id')}",
            "deal_id": deal.get("id"),
            "buyer_id": buyer.get("buyer_id") or buyer.get("id"),
            "buyer_name": buyer.get("buyer_name") or buyer.get("name"),
            "property_address": deal.get("property_address"),
            "match_score": match_score,
            "match_band": buyer.get("match_band"),
            "message": draft.get("message"),
            "status": "PENDING_APPROVAL",
            "created_at": datetime.utcnow().isoformat(),
            "requires_human_approval": True,
        })

    return {
        "deal_id": deal.get("id"),
        "property_address": deal.get("property_address"),
        "queue_count": len(queue_items),
        "approval_queue": queue_items,
        "send_blocked_until_approved": True,
    }


def approve_buyer_outreach(queue_item: Dict[str, Any], approved_by: str) -> Dict[str, Any]:
    return {
        **queue_item,
        "status": "APPROVED_TO_SEND",
        "approved_by": approved_by,
        "approved_at": datetime.utcnow().isoformat(),
        "send_allowed": True,
    }


def reject_buyer_outreach(queue_item: Dict[str, Any], rejected_by: str, reason: str) -> Dict[str, Any]:
    return {
        **queue_item,
        "status": "REJECTED",
        "rejected_by": rejected_by,
        "rejected_at": datetime.utcnow().isoformat(),
        "rejection_reason": reason,
        "send_allowed": False,
    }
