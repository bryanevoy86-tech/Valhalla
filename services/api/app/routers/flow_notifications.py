# services/api/app/routers/flow_notifications.py

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.geo import infer_province_market
from app.models.deal import Deal
from app.models.match import Buyer, DealBrief
from app.schemas.notifications_flow import (
    BuyerNotification,
    NotifyDealPartiesRequest,
    NotifyDealPartiesResponse,
    SellerNotification,
)
from app.routers.flow_lead_to_deal import _score_buyer_for_deal  # reuse matcher
from app.services.buyer_liquidity import liquidity_score
from app.services.kpi import emit_kpi

router = APIRouter(
    prefix="/flow",
    tags=["Flow", "Notifications"],
)


def _get_deal_and_brief(
    db: Session,
    backend_deal_id: int,
) -> tuple[Deal, Optional[DealBrief]]:
    deal: Optional[Deal] = (
        db.query(Deal)
        .filter(Deal.id == backend_deal_id)
        .first()
    )
    if deal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with id {backend_deal_id} not found.",
        )

    deal_brief: Optional[DealBrief] = (
        db.query(DealBrief)
        .filter(DealBrief.id == backend_deal_id)
        .first()
    )

    return deal, deal_brief


def _build_seller_notification(
    db: Session,
    deal: Deal,
    deal_brief: Optional[DealBrief],
) -> SellerNotification:
    lead_obj = getattr(deal, "lead", None)

    to_email = getattr(lead_obj, "email", None) if lead_obj else None
    to_phone = getattr(lead_obj, "phone", None) if lead_obj else None
    seller_name = getattr(lead_obj, "name", "there") if lead_obj else "there"

    # --- Infer province/market for policy context ---
    province = None
    market = None
    liq_score = None
    
    if deal_brief:
        region = getattr(deal_brief, "region", None)
        headline = getattr(deal_brief, "headline", None)
        property_type = getattr(deal_brief, "property_type", None)
        
        try:
            province, market = infer_province_market(region, None)
            if province and property_type:
                liq_score = liquidity_score(db, province, market or "ALL", property_type)
        except Exception:
            # Non-blocking: geo inference or liquidity fetch failed
            pass
    else:
        headline = None
        region = None
        property_type = None

    subject = "Update on your property and our offer"
    body_lines = [
        f"Hi {seller_name},",
        "",
        "Thanks again for speaking with us about your property.",
    ]

    if headline:
        body_lines.append(f"We have your deal noted as: {headline}.")
    elif region or property_type:
        body_lines.append(
            f"We're reviewing your {property_type or 'property'} in {region or 'your area'}."
        )

    price = getattr(deal, "offer", None) or getattr(deal, "price", None)
    if price is not None:
        body_lines.append(
            f"Right now, we're working off a working number around ${price:,.0f}, "
            "based on the condition and repairs we discussed."
        )

    body_lines.extend(
        [
            "",
            "Our next step is to finish reviewing the numbers and confirm if we can "
            "move forward at that price, or whether we need to adjust based on "
            "repairs, timeline, or terms.",
            "",
            "If you have any questions or if something changes on your side "
            "(timeline, tenants, access, etc.), just reply to this message or call us.",
            "",
            "Talk soon,",
            "Valhalla Legacy Inc",
        ]
    )

    body_text = "\n".join(body_lines)

    return SellerNotification(
        to_email=to_email,
        to_phone=to_phone,
        channel_hint="email_or_sms",
        subject=subject,
        body_text=body_text,
        body_markdown=None,
        meta={
            "lead_id": str(lead_obj.id) if lead_obj else "",
            "deal_id": str(deal.id),
            "province": province,
            "market": market,
            "liquidity_score": liq_score,
        },
    )


def _build_buyer_notifications(
    db: Session,
    deal: Deal,
    deal_brief: Optional[DealBrief],
    min_score: float,
    max_buyers: int,
) -> List[BuyerNotification]:
    if deal_brief is None:
        return []

    # --- Infer province/market for context ---
    province = None
    market = None
    liq_score = None
    
    region = getattr(deal_brief, "region", None)
    property_type = getattr(deal_brief, "property_type", None)
    
    try:
        province, market = infer_province_market(region, None)
        if province and property_type:
            liq_score = liquidity_score(db, province, market or "ALL", property_type)
    except Exception:
        # Non-blocking: geo/liquidity fetch failed
        pass

    buyers = db.query(Buyer).filter(Buyer.active.is_(True)).all()
    candidates = []

    for buyer in buyers:
        candidate = _score_buyer_for_deal(buyer, deal_brief)
        if candidate is None:
            continue
        if candidate.score < min_score:
            continue
        candidates.append((buyer, candidate))

    # Sort by score descending
    candidates.sort(key=lambda pair: pair[1].score, reverse=True)
    candidates = candidates[:max_buyers]

    notifications: List[BuyerNotification] = []

    for buyer, match in candidates:
        buyer_name = getattr(buyer, "name", "Investor")
        to_email = getattr(buyer, "email", None)
        to_phone = getattr(buyer, "phone", None)

        headline = getattr(deal_brief, "headline", None) or "New deal opportunity"
        region_display = getattr(deal_brief, "region", "your target markets")
        property_type_display = getattr(deal_brief, "property_type", "property")
        price = getattr(deal_brief, "price", None)

        subject = f"Deal opportunity: {property_type_display} in {region_display}"

        body_lines = [
            f"Hi {buyer_name},",
            "",
            "We've got a new deal that looks like a fit for your buy box:",
            "",
            f"- Headline: {headline}",
            f"- Region: {region_display}",
            f"- Type: {property_type_display}",
        ]

        if price is not None:
            body_lines.append(f"- Price: ${price:,.0f}")

        body_lines.extend(
            [
                f"- Match score: {match.score:.0%}",
                "",
                "If you'd like more details or to walk through the numbers, "
                "reply to this message and we'll line up the next steps.",
                "",
                "Valhalla Legacy Inc",
            ]
        )

        body_text = "\n".join(body_lines)

        notifications.append(
            BuyerNotification(
                buyer_id=buyer.id,
                buyer_name=buyer_name,
                to_email=to_email,
                to_phone=to_phone,
                channel_hint="email_or_sms",
                subject=subject,
                body_text=body_text,
                body_markdown=None,
                match_score=match.score,
                meta={
                    "deal_id": str(deal.id),
                    "deal_brief_id": str(deal_brief.id),
                    "province": province,
                    "market": market,
                    "liquidity_score": liq_score,
                },
            )
        )

    return notifications


@router.post(
    "/notify_deal_parties",
    response_model=NotifyDealPartiesResponse,
    status_code=status.HTTP_200_OK,
    summary="Prepare notifications for seller and matched buyers",
    description=(
        "Given a backend_deal_id, builds suggested notification payloads for:\n"
        "- the seller (update on offer / next steps)\n"
        "- matched buyers (deal opportunity)\n"
        "This does NOT send anything; it prepares content for email/SMS/Heimdall."
    ),
)
def notify_deal_parties(
    payload: NotifyDealPartiesRequest,
    db: Session = Depends(get_db),
) -> NotifyDealPartiesResponse:
    deal, deal_brief = _get_deal_and_brief(db, payload.backend_deal_id)

    seller_notification: Optional[SellerNotification] = None
    if payload.include_seller:
        seller_notification = _build_seller_notification(db, deal, deal_brief)

    buyer_notifications: List[BuyerNotification] = []
    if payload.include_buyers:
        buyer_notifications = _build_buyer_notifications(
            db=db,
            deal=deal,
            deal_brief=deal_brief,
            min_score=payload.min_buyer_score,
            max_buyers=payload.max_buyers,
        )

    # --- Emit KPI: notifications prepared ---
    corr_id = f"notifications:{deal.id}"
    emit_kpi(
        db, "NOTIFICATIONS", "prepared",
        success=True,
        actor="system",
        correlation_id=corr_id,
        detail={
            "deal_id": deal.id,
            "seller_notified": seller_notification is not None,
            "buyer_count": len(buyer_notifications),
        },
    )

    notes_parts = []
    if seller_notification:
        notes_parts.append("Seller notification prepared.")
    if buyer_notifications:
        notes_parts.append(f"{len(buyer_notifications)} buyer notifications prepared.")
    if not notes_parts:
        notes_parts.append("No notifications prepared (check flags or data).")

    notes = " ".join(notes_parts)

    metadata = {
        "backend_deal_id": str(payload.backend_deal_id),
        "include_seller": str(payload.include_seller),
        "include_buyers": str(payload.include_buyers),
        "min_buyer_score": str(payload.min_buyer_score),
        "max_buyers": str(payload.max_buyers),
    }

    return NotifyDealPartiesResponse(
        backend_deal_id=payload.backend_deal_id,
        seller_notification=seller_notification,
        buyer_notifications=buyer_notifications,
        notes=notes,
        metadata=metadata,
    )
