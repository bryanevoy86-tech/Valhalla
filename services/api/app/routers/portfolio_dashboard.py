"""Private portfolio views over canonical deals and their linked records."""

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.models.deal import Deal, DealBriefLink
from app.models.freeze_events import FreezeEvent
from app.models.match import DealBrief
from app.offers.models import Offer
from app.schemas.portfolio import (
    DealStatusCounts,
    FreezeSummaryCounts,
    PortfolioDealSnapshot,
    PortfolioDealsResponse,
    PortfolioSummary,
)
from app.services.freeze_events import FREEZE_EVENT_TYPES

router = APIRouter(
    prefix="/portfolio", tags=["Portfolio"],
    dependencies=[Depends(require_prime_control_key)],
)


def _portfolio(db: Session) -> PortfolioDealsResponse:
    rows = (
        db.query(Deal, DealBrief)
        .outerjoin(DealBriefLink, DealBriefLink.deal_id == Deal.id)
        .outerjoin(DealBrief, DealBriefLink.brief_id == DealBrief.id)
        .order_by(Deal.id)
        .all()
    )
    offers = {}
    for offer in db.query(Offer).order_by(Offer.created_at.desc(), Offer.id.desc()):
        offers.setdefault(offer.deal_id, offer.offer_price)
    events = (
        db.query(FreezeEvent)
        .filter(FreezeEvent.event_type.in_(FREEZE_EVENT_TYPES))
        .order_by(FreezeEvent.created_at.desc(), FreezeEvent.id.desc())
        .all()
    )
    freeze_counts = FreezeSummaryCounts(total_events=len(events))
    latest_active = {}
    for event in events:
        match event.severity:
            case "info":
                freeze_counts.info += 1
            case "warn":
                freeze_counts.warn += 1
            case "critical":
                freeze_counts.critical += 1
        if not event.is_completed:
            freeze_counts.unresolved += 1
            latest_active.setdefault(event.deal_id, event)

    counts = DealStatusCounts()
    estimates: dict[str, Decimal] = {}
    snapshots = []
    for deal, brief in rows:
        state = deal.status
        category = "sold" if state == "closed" else state
        if category not in DealStatusCounts.model_fields:
            category = "draft"
        setattr(counts, category, getattr(counts, category) + 1)

        offer = offers.get(deal.id)
        price = brief.price if brief else None
        cost = offer if offer is not None else price
        repairs = deal.estimated_repair_cost
        freeze = latest_active.get(str(deal.id))
        snapshots.append(PortfolioDealSnapshot(
            id=deal.id, status=state, headline=deal.title,
            region=brief.region if brief else None,
            property_type=brief.property_type if brief else None,
            price=price, arv=deal.arv, repairs=repairs, offer=offer,
            mao=deal.max_allowable_offer, has_freeze=freeze is not None,
            freeze_severity=freeze.severity if freeze else None,
        ))
        if cost is not None and deal.arv is not None and repairs is not None:
            bucket = "active" if category in {"active", "under_contract"} else category
            if bucket in {"active", "sold"}:
                estimates[bucket] = estimates.get(bucket, Decimal(0)) + deal.arv - cost - repairs

    return PortfolioDealsResponse(
        deals=snapshots,
        summary=PortfolioSummary(
            total_deals=len(rows),
            status_counts=counts,
            estimated_gross_profit_active=estimates.get("active"),
            estimated_gross_profit_sold=estimates.get("sold"),
            freeze_counts=freeze_counts,
            notes="Estimates use offer or asking price and repairs. They exclude holding costs, closing costs and taxes.",
        ),
    )


@router.get("/summary", response_model=PortfolioSummary)
def portfolio_summary(db: Session = Depends(get_db)) -> PortfolioSummary:
    return _portfolio(db).summary


@router.get("/deals", response_model=PortfolioDealsResponse)
def portfolio_deals(db: Session = Depends(get_db)) -> PortfolioDealsResponse:
    return _portfolio(db)
