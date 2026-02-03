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


@router.post("/test/insert-manitoba-data")
def insert_manitoba_data(
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """
    Insert realistic Manitoba test data:
    - MANI001: Local pickup (no shipping) → high margin
    - MANI002: Cross-province shipped → moderate margin
    - MANI003: Marginal spread → should be rejected by new policy
    """
    from app.models.market_feed_event import MarketFeedEvent
    
    # Clear old demo data first
    db.query(MarketFeedEvent).filter(MarketFeedEvent.sku.in_(['SKU123', 'SKU999', 'SKU777'])).delete()
    
    test_events = [
        # MANI001: Local pickup (no shipping cost) - WINNIPEG to CALGARY local buyers
        # Buy: $45 (local Winnipeg seller), Sell: $89 (Calgary buyer, local pickup)
        # Net: $89 - $45 - (89*0.10 fee) - $0 shipping = $44 - $8.90 = $35.10 ✓ PASS
        MarketFeedEvent(source='kijiji_buy', sku='MANI001', title='Vintage Tool Set', venue='BUY', price=45.00, currency='CAD', url='http://kijiji.ca/buy1'),
        MarketFeedEvent(source='facebook_sell', sku='MANI001', title='Vintage Tool Set', venue='SELL', price=89.00, currency='CAD', url='http://facebook.com/sell1'),
        
        # MANI002: Cross-province shipped (realistic $18 shipping)
        # Buy: $75 (Toronto supplier), Sell: $155 (Vancouver buyer shipped)
        # Net: $155 - $75 - (155*0.10 fee) - $18 shipping = $80 - $15.50 - $18 = $46.50 ✓ PASS
        MarketFeedEvent(source='alibaba_buy', sku='MANI002', title='Home Decor Item', venue='BUY', price=75.00, currency='CAD', url='http://alibaba.com/buy2'),
        MarketFeedEvent(source='ebay_sell', sku='MANI002', title='Home Decor Item', venue='SELL', price=155.00, currency='CAD', url='http://ebay.ca/sell2'),
        
        # MANI003: Marginal spread (new policy should reject)
        # Buy: $120, Sell: $145
        # Net: $145 - $120 - (145*0.10 fee) - $10 shipping = $25 - $14.50 - $10 = $0.50 ✗ FAIL (< $25 min_profit)
        MarketFeedEvent(source='craigslist_buy', sku='MANI003', title='Used Electronics', venue='BUY', price=120.00, currency='CAD', url='http://craigslist.ca/buy3'),
        MarketFeedEvent(source='kijiji_sell', sku='MANI003', title='Used Electronics', venue='SELL', price=145.00, currency='CAD', url='http://kijiji.ca/sell3'),
    ]
    
    try:
        db.add_all(test_events)
        db.commit()
        return {
            "ok": True,
            "inserted": len(test_events),
            "message": "Manitoba test data inserted",
            "note": "Run POST /api/arbitrage/scan - expect 2 opportunities (MANI001 $35.10, MANI002 $46.50), reject MANI003"
        }
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}
    }

