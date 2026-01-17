# services/api/app/routers/portfolio_dashboard.py

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.deal import Deal
from app.freeze.models import FreezeEvent
from app.models.match import DealBrief
from app.schemas.portfolio import (
    DealStatusCounts,
    FreezeSummaryCounts,
    PortfolioDealSnapshot,
    PortfolioDealsResponse,
    PortfolioSummary,
)

router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"],
)


def _dec(val: object | None) -> Optional[Decimal]:
    if val is None:
        return None
    try:
        return Decimal(str(val))
    except Exception:
        return None


def _status_counts(deals: List[Deal]) -> DealStatusCounts:
    counts = DealStatusCounts()
    for d in deals:
        s = (d.status or "").lower()
        if s == "draft":
            counts.draft += 1
        elif s == "active":
            counts.active += 1
        elif s == "under_contract":
            counts.under_contract += 1
        elif s == "sold":
            counts.sold += 1
        elif s == "archived":
            counts.archived += 1
        else:
            counts.draft += 1  # treat unknown as draft for now
    return counts


def _freeze_counts(events: List[FreezeEvent]) -> FreezeSummaryCounts:
    counts = FreezeSummaryCounts(total_events=len(events))
    for e in events:
        severity = (e.severity or "").lower()
        if severity == "info":
            counts.info += 1
        elif severity == "warn":
            counts.warn += 1
        elif severity == "critical":
            counts.critical += 1
        else:
            counts.info += 1

        if e.resolved_at is None:
            counts.unresolved += 1

    return counts


def _latest_freeze_for_deal(
    deal_freezes: List[FreezeEvent],
) -> Tuple[bool, Optional[str]]:
    if not deal_freezes:
        return False, None
    # Assume events already sorted by created_at desc if we want; for now just pick the last.
    latest = sorted(deal_freezes, key=lambda e: e.created_at, reverse=True)[0]
    return True, latest.severity


@router.get(
    "/summary",
    response_model=PortfolioSummary,
    status_code=status.HTTP_200_OK,
    summary="Portfolio-level summary for all deals",
    description=(
        "Returns a high-level overview of all deals in the system: status counts, "
        "rough gross profit estimates, and freeze event counts."
    ),
)
def portfolio_summary(
    db: Session = Depends(get_db),
) -> PortfolioSummary:
    deals: List[Deal] = db.query(Deal).all()
    total_deals = len(deals)

    status_c = _status_counts(deals)

    # Freeze events
    freeze_events: List[FreezeEvent] = db.query(FreezeEvent).all()
    freeze_c = _freeze_counts(freeze_events)

    # Rough gross profit estimates (best-effort only)
    est_active = Decimal("0")
    est_sold = Decimal("0")
    has_active = False
    has_sold = False

    for d in deals:
        arv = _dec(getattr(d, "arv", None))
        price = _dec(getattr(d, "price", None) or getattr(d, "offer", None))
        repairs = _dec(getattr(d, "repairs", None))

        if arv is not None and price is not None:
            total_cost = price + (repairs or Decimal("0"))
            rough_profit = arv - total_cost

            if (d.status or "").lower() in {"active", "under_contract"}:
                est_active += rough_profit
                has_active = True
            elif (d.status or "").lower() == "sold":
                est_sold += rough_profit
                has_sold = True

    est_active_val: Optional[Decimal] = est_active if has_active else None
    est_sold_val: Optional[Decimal] = est_sold if has_sold else None

    notes = (
        "Estimates are rough and based on ARV, price/offer, and repairs only; "
        "they do not include holding costs, closing costs, or tax."
    )

    debug = {
        "total_deals": str(total_deals),
        "has_active_estimates": str(has_active),
        "has_sold_estimates": str(has_sold),
        "freeze_events_total": str(freeze_c.total_events),
    }

    return PortfolioSummary(
        total_deals=total_deals,
        status_counts=status_c,
        estimated_gross_profit_active=est_active_val,
        estimated_gross_profit_sold=est_sold_val,
        freeze_counts=freeze_c,
        notes=notes,
        debug=debug,
    )


@router.get(
    "/deals",
    response_model=PortfolioDealsResponse,
    status_code=status.HTTP_200_OK,
    summary="Detailed deals + portfolio summary",
    description=(
        "Returns the portfolio summary plus a list of all deals with: status, "
        "headline/region/type, key numbers, and latest freeze severity (if any)."
    ),
)
def portfolio_deals(
    db: Session = Depends(get_db),
) -> PortfolioDealsResponse:
    deals: List[Deal] = db.query(Deal).all()
    deal_ids = [d.id for d in deals]

    # Map DealBriefs by id (our convention: DealBrief.id == backend_deal_id when created by pipeline)
    briefs: List[DealBrief] = (
        db.query(DealBrief)
        .filter(DealBrief.id.in_(deal_ids))
        .all()
    )
    briefs_map = {b.id: b for b in briefs}

    # Map freeze events by backend_deal_id (from payload JSONB, best-effort)
    freeze_events: List[FreezeEvent] = db.query(FreezeEvent).all()
    freeze_by_deal: dict[int, List[FreezeEvent]] = {}
    for e in freeze_events:
        try:
            backend_deal_id = int(e.payload.get("backend_deal_id"))  # type: ignore[call-arg]
        except Exception:
            backend_deal_id = None
        if not backend_deal_id:
            continue
        freeze_by_deal.setdefault(backend_deal_id, []).append(e)

    snapshots: List[PortfolioDealSnapshot] = []

    for d in deals:
        brief = briefs_map.get(d.id)
        has_freeze, freeze_severity = _latest_freeze_for_deal(
            freeze_by_deal.get(d.id, []),
        )

        snapshot = PortfolioDealSnapshot(
            id=d.id,
            status=d.status,
            region=getattr(brief, "region", None) if brief else None,
            property_type=getattr(brief, "property_type", None) if brief else None,
            price=_dec(getattr(d, "price", None) or getattr(d, "offer", None)),
            arv=_dec(getattr(d, "arv", None)),
            repairs=_dec(getattr(d, "repairs", None)),
            offer=_dec(getattr(d, "offer", None)),
            mao=_dec(getattr(d, "mao", None)),
            headline=getattr(brief, "headline", None) if brief else None,
            has_freeze=has_freeze,
            freeze_severity=freeze_severity,
        )
        snapshots.append(snapshot)

    summary = portfolio_summary(db=db)

    return PortfolioDealsResponse(
        summary=summary,
        deals=snapshots,
    )
