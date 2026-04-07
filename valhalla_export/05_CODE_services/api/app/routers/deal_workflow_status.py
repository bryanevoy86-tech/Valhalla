# services/api/app/routers/deal_workflow_status.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.deal import Deal
from app.models.match import DealBrief, Buyer
from app.models.freeze_events import FreezeEvent

router = APIRouter(
    prefix="/workflow",
    tags=["Workflow", "DealStatus"],
)


def _freeze_status_for_deal(db: Session, backend_deal_id: int) -> Dict[str, Any]:
    """
    Gather freeze_events affecting this deal, if any.
    """
    events: List[FreezeEvent] = (
        db.query(FreezeEvent)
        .filter(FreezeEvent.payload["backend_deal_id"].as_integer() == backend_deal_id)
        .order_by(FreezeEvent.created_at.desc())
        .all()
    )

    if not events:
        return {
            "has_freeze": False,
            "latest": None,
        }

    latest = events[0]
    return {
        "has_freeze": True,
        "latest": {
            "id": latest.id,
            "created_at": latest.created_at.isoformat(),
            "severity": latest.severity,
            "event_type": latest.event_type,
            "reason": latest.reason,
            "resolved_at": latest.resolved_at.isoformat() if latest.resolved_at else None,
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

    # Try to locate DealBrief with same id or via basic matching.
    # (You can adjust this linkage strategy based on your schema.)
    deal_brief: Optional[DealBrief] = (
        db.query(DealBrief)
        .filter(DealBrief.id == backend_deal_id)
        .first()
    )

    # Linked lead
    lead_obj = None
    if getattr(deal, "lead", None) is not None:
        lead_obj = deal.lead

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
    ready_for_marketing = (
        deal_brief is not None and not freeze_status.get("has_freeze", False)
    )
    blocked = freeze_status.get("has_freeze", False)

    return {
        "deal": {
            "id": deal.id,
            "status": deal.status,
            "price": deal.price,
            "arv": getattr(deal, "arv", None),
            "repairs": getattr(deal, "repairs", None),
            "offer": getattr(deal, "offer", None),
            "mao": getattr(deal, "mao", None),
        },
        "lead": {
            "id": getattr(lead_obj, "id", None),
            "name": getattr(lead_obj, "name", None),
            "email": getattr(lead_obj, "email", None),
            "phone": getattr(lead_obj, "phone", None),
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
            "ready_for_marketing": ready_for_marketing,
            "blocked_by_freeze": blocked,
        },
    }
