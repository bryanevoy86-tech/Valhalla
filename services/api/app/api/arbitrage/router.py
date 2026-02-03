from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_builder_key

router = APIRouter(prefix="/arbitrage", tags=["arbitrage"])


@router.get("/health")
def arbitrage_health(db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    """Health check for arbitrage engine."""
    return {"ok": True, "service": "arbitrage", "mode": "SANDBOX_SIM_ONLY"}


@router.post("/scan")
def run_scan(
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """Scan for arbitrage opportunities (simulation only)."""
    from app.models.arbitrage_opportunity import ArbitrageOpportunity
    from app.models.arbitrage_sim_trade import ArbitrageSimTrade
    from app.engines.arbitrage.engine import scan_arbitrage, ArbitragePolicy
    
    policy = ArbitragePolicy()
    result = scan_arbitrage(db, policy)
    return result


@router.get("/opportunities")
def list_opportunities(
    status: str = Query("OPEN"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """List detected arbitrage opportunities."""
    from app.models.arbitrage_opportunity import ArbitrageOpportunity
    
    rows = (
        db.query(ArbitrageOpportunity)
        .filter(ArbitrageOpportunity.status == status)
        .order_by(ArbitrageOpportunity.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "sku": r.sku,
            "buy_source": r.buy_source,
            "buy_price": r.buy_price,
            "sell_source": r.sell_source,
            "sell_price": r.sell_price,
            "net_profit": r.net_profit,
            "roi": r.roi,
            "confidence": r.confidence,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/scorecard")
def scorecard(
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """Arbitrage scorecard: performance summary."""
    from app.models.arbitrage_opportunity import ArbitrageOpportunity
    from app.models.arbitrage_sim_trade import ArbitrageSimTrade
    
    open_ops = db.query(ArbitrageOpportunity).filter(ArbitrageOpportunity.status == "OPEN").count()
    sim_count = db.query(ArbitrageSimTrade).count()

    # Basic profitability stats
    sims = db.query(ArbitrageSimTrade).all()
    if sims:
        total_profit = sum(s.net_profit for s in sims)
        avg_roi = sum(s.roi for s in sims) / max(1, len(sims))
    else:
        total_profit = 0.0
        avg_roi = 0.0

    return {
        "engine": "arbitrage",
        "mode": "SANDBOX_SIM_ONLY",
        "open_opportunities": open_ops,
        "sim_trades": sim_count,
        "sim_total_profit": round(total_profit, 2),
        "sim_avg_roi": round(avg_roi, 4),
        "note": "No real execution. No capital moves. Observation + simulation only.",
    }


@router.post("/test/insert-demo-data")
def insert_demo_data(
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """
    Insert demo feed events for Phase A testing.
    
    Demo data:
    - SKU123: $100 buy → $155 sell (good spread, should pass)
    - SKU999: $120 buy → $130 sell (bad spread, too small)
    - SKU777: $80 buy → $150 sell (strong spread, should pass)
    """
    from app.models.market_feed_event import MarketFeedEvent
    
    test_events = [
        # GOOD SPREAD
        MarketFeedEvent(source='manual_buy', sku='SKU123', title='Test Item A', venue='BUY', price=100.00, currency='CAD', url='http://buy.example/itemA'),
        MarketFeedEvent(source='manual_sell', sku='SKU123', title='Test Item A', venue='SELL', price=155.00, currency='CAD', url='http://sell.example/itemA'),
        # BAD SPREAD
        MarketFeedEvent(source='manual_buy', sku='SKU999', title='Test Item B', venue='BUY', price=120.00, currency='CAD', url='http://buy.example/itemB'),
        MarketFeedEvent(source='manual_sell', sku='SKU999', title='Test Item B', venue='SELL', price=130.00, currency='CAD', url='http://sell.example/itemB'),
        # STRONG SPREAD
        MarketFeedEvent(source='manual_buy', sku='SKU777', title='Test Item C', venue='BUY', price=80.00, currency='CAD', url='http://buy.example/itemC'),
        MarketFeedEvent(source='manual_sell', sku='SKU777', title='Test Item C', venue='SELL', price=150.00, currency='CAD', url='http://sell.example/itemC'),
    ]
    
    existing = db.query(MarketFeedEvent).filter(MarketFeedEvent.sku.in_(['SKU123', 'SKU999', 'SKU777'])).count()
    if existing > 0:
        return {"ok": True, "message": "Demo data already exists", "existing_count": existing, "hint": "Run POST /api/arbitrage/scan to process"}
    
    try:
        db.add_all(test_events)
        db.commit()
        return {"ok": True, "inserted": len(test_events), "message": "Demo feed events inserted"}
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}
    }

