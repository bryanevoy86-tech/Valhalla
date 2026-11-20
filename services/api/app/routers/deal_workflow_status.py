# services/api/app/routers/deal_workflow_status.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.leads.models import Lead
from app.models.deal import Deal
from app.models.match import DealBrief, Buyer
from app.services.deal_context import latest_offer, linked_brief
from app.services.freeze_events import get_deal_freezes

router = APIRouter(
    prefix="/workflow",
    tags=["Workflow", "DealStatus"],
    dependencies=[Depends(require_prime_control_key)],
)


def _freeze_status_for_deal(db: Session, backend_deal_id: int) -> Dict[str, Any]:
    """
    Gather freeze_events affecting this deal, if any.
    """
    events = get_deal_freezes(db, backend_deal_id)

    if not events:
        return {
            "has_freeze": False,
            "latest": None,
        }

    latest = events[0]
    return {
        "has_freeze": any(not entry.is_completed for entry in events),
        "latest": {
            "id": latest.id,
            "created_at": latest.created_at.isoformat(),
            "severity": latest.severity,
            "event_type": latest.event_type,
            "reason": latest.reason or latest.notes,
            "resolved_at": latest.completed_at.isoformat() if latest.completed_at else None,
        },
        "count": len(events),
    }


def _buyer_match_summary(db: Session, deal_brief: DealBrief) -> Dict[str, Any]:
    """
    Very light summary: how many active buyers look like they *might* match
    this deal based on simple region/property_type filters.

    This is not the full matcher; it's a quick status indicator.
    """
    # Region/type are optional — if missing, just report unknown.
    if not deal_brief.region and not deal_brief.property_type:
        return {
            "status": "unknown",
            "reason": "DealBrief missing region/property_type.",
            "candidate_count": None,
        }

    query = db.query(Buyer).filter(Buyer.active.is_(True))

    if deal_brief.region:
        query = query.filter(Buyer.regions.ilike(f"%{deal_brief.region}%"))

    if deal_brief.property_type:
        query = query.filter(Buyer.property_types.ilike(f"%{deal_brief.property_type}%"))

    count = query.count()

    return {
        "status": "ok" if count > 0 else "no_candidates",
        "candidate_count": count,
    }


@router.get(
    "/deal_status/{backend_deal_id}",
    summary="Get full workflow status for a deal",
    description=(
        "Returns a unified status view for a given backend Deal:\n"
        "- deal row (backend)\n"
        "- DealBrief (match system)\n"
        "- linked lead (if available)\n"
        "- freeze_events affecting the deal\n"
        "- coarse buyer match readiness\n"
    ),
)
def get_deal_workflow_status(
    backend_deal_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    # Backend Deal
    deal: Optional[Deal] = db.query(Deal).filter(Deal.id == backend_deal_id).first()
    if deal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with id {backend_deal_id} not found.",
        )

    deal_brief = linked_brief(db, backend_deal_id)
    lead_obj = db.get(Lead, deal.lead_id)
    offer = latest_offer(db, backend_deal_id)

    # Freeze status
    freeze_status = _freeze_status_for_deal(db, backend_deal_id)

    # Buyer match readiness
    buyer_summary: Dict[str, Any]
    if deal_brief is not None:
        buyer_summary = _buyer_match_summary(db, deal_brief)
    else:
        buyer_summary = {
            "status": "unknown",
            "reason": "No DealBrief found for this backend_deal_id.",
            "candidate_count": None,
        }

    # High-level flags
    blocked = freeze_status.get("has_freeze", False)

    return {
        "deal": {
            "id": deal.id,
            "status": deal.status,
            "price": deal_brief.price if deal_brief is not None else None,
            "arv": getattr(deal, "arv", None),
            "repairs": deal.estimated_repair_cost,
            "offer": offer.offer_price if offer is not None else None,
            "mao": deal.max_allowable_offer,
        },
        "lead": {
            "id": getattr(lead_obj, "id", None),
            "name": lead_obj.lead_name,
            "email": lead_obj.lead_email,
            "phone": lead_obj.lead_phone,
        }
        if lead_obj is not None
        else None,
        "deal_brief": {
            "id": deal_brief.id,
            "headline": deal_brief.headline,
            "region": deal_brief.region,
            "property_type": deal_brief.property_type,
            "price": deal_brief.price,
            "status": deal_brief.status,
        }
        if deal_brief is not None
        else None,
        "freeze": freeze_status,
        "buyer_readiness": buyer_summary,
        "flags": {
            "ready_for_marketing": False,
            "blocked_by_freeze": blocked,
        },
    }
