from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.models.market_feed_event import MarketFeedEvent
from app.models.arbitrage_opportunity import ArbitrageOpportunity
from app.models.arbitrage_sim_trade import ArbitrageSimTrade


def _env_float(name: str, default: float) -> float:
    """Read float from env var, return default if missing or invalid."""
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return default
    try:
        return float(v)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    """Read int from env var, return default if missing or invalid."""
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return default
    try:
        return int(v)
    except ValueError:
        return default


@dataclass
class ArbitragePolicy:
    # Phase A: configurable via Render env vars, sensible Manitoba defaults
    min_roi: float = field(default_factory=lambda: _env_float("ARB_MIN_ROI", 0.05))
    min_profit: float = field(default_factory=lambda: _env_float("ARB_MIN_PROFIT", 25.0))
    assumed_fee_rate: float = field(default_factory=lambda: _env_float("ARB_FEE_RATE", 0.10))
    assumed_shipping: float = field(default_factory=lambda: _env_float("ARB_SHIPPING", 10.0))
    max_age_hours: int = field(default_factory=lambda: _env_int("ARB_MAX_AGE_HOURS", 72))


def _estimate_fees(buy_price: float, sell_price: float, policy: ArbitragePolicy) -> float:
    # simplest possible: fee based on sell price
    return sell_price * policy.assumed_fee_rate


def scan_arbitrage(db: Session, policy: ArbitragePolicy) -> dict:
    """
    Phase A:
    - find cheapest BUY and highest SELL for same SKU across sources
    - compute net profit + ROI
    - if passes policy, create opportunity
    - also create simulated trade (paper)
    """

    # Load recent feed events
    rows = db.query(MarketFeedEvent).all()
    if not rows:
        return {"ok": True, "scanned": 0, "created_opportunities": 0, "created_sim_trades": 0}

    by_sku = {}
    for r in rows:
        by_sku.setdefault(r.sku, []).append(r)

    created_ops = 0
    created_sims = 0

    for sku, events in by_sku.items():
        # Find best buy (lowest price) and best sell (highest price)
        best_buy = min(events, key=lambda x: x.price)
        best_sell = max(events, key=lambda x: x.price)

        if best_sell.price <= best_buy.price:
            continue

        fees = _estimate_fees(best_buy.price, best_sell.price, policy)
        shipping = policy.assumed_shipping
        gross = best_sell.price - best_buy.price
        net = gross - fees - shipping
        roi = net / best_buy.price if best_buy.price > 0 else -1.0

        if net < policy.min_profit or roi < policy.min_roi:
            continue

        # Confidence: basic sanity — wider spread + ROI gives higher confidence (bounded)
        conf = max(0.1, min(0.95, 0.4 + (roi * 3.0)))

        op = ArbitrageOpportunity(
            sku=sku,
            buy_source=best_buy.source,
            buy_price=best_buy.price,
            buy_url=best_buy.url,
            sell_source=best_sell.source,
            sell_price=best_sell.price,
            sell_url=best_sell.url,
            fees_estimate=fees,
            shipping_estimate=shipping,
            gross_spread=gross,
            net_profit=net,
            roi=roi,
            confidence=conf,
            reason=f"best_buy={best_buy.source} best_sell={best_sell.source}",
            status="OPEN",
        )
        db.add(op)
        db.flush()  # so we can link sim trade

        sim = ArbitrageSimTrade(
            sku=sku,
            buy_price=best_buy.price,
            sell_price=best_sell.price,
            fees=fees,
            shipping=shipping,
            net_profit=net,
            roi=roi,
            linked_opportunity_id=op.id,
            notes="SIM ONLY (Phase A)",
        )
        db.add(sim)

        created_ops += 1
        created_sims += 1

    db.commit()

    return {
        "ok": True,
        "scanned": len(by_sku),
        "created_opportunities": created_ops,
        "created_sim_trades": created_sims,
        "policy": {
            "min_roi": policy.min_roi,
            "min_profit": policy.min_profit,
            "assumed_fee_rate": policy.assumed_fee_rate,
            "assumed_shipping": policy.assumed_shipping,
        },
    }
