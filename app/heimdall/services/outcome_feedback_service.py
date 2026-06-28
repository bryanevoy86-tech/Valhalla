from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.heimdall.models.persistence import HeimdallDeal


def record_deal_outcome(
    db: Session,
    deal_id: str,
    outcome_payload: Dict[str, Any],
) -> Dict[str, Any]:
    deal = (
        db.query(HeimdallDeal)
        .filter(HeimdallDeal.id == deal_id)
        .first()
    )

    if not deal:
        return {
            "status": "ERROR",
            "reason": "Deal not found.",
        }

    existing = deal.data or {}
    existing["outcome_feedback"] = {
        "closed": outcome_payload.get("closed"),
        "assignment_fee": outcome_payload.get("assignment_fee"),
        "actual_arv": outcome_payload.get("actual_arv"),
        "actual_repair_cost": outcome_payload.get("actual_repair_cost"),
        "buyer_closed": outcome_payload.get("buyer_closed"),
        "seller_responsive": outcome_payload.get("seller_responsive"),
        "heimdall_prediction_accuracy": outcome_payload.get(
            "heimdall_prediction_accuracy"
        ),
        "mistakes": outcome_payload.get("mistakes", []),
        "lessons": outcome_payload.get("lessons", []),
        "recorded_at": datetime.utcnow().isoformat(),
    }

    deal.data = existing
    db.commit()
    db.refresh(deal)

    return {
        "status": "OUTCOME_RECORDED",
        "deal_id": deal.id,
    }
