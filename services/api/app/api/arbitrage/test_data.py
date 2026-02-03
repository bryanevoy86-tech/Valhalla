"""
Temporary endpoint to insert arbitrage test data (for Phase A verification).
Protected by builder key.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_builder_key
from app.models.market_feed_event import MarketFeedEvent

router = APIRouter(prefix="/arbitrage", tags=["arbitrage-test"])


@router.post("/test/insert-demo-data")
def insert_demo_data(
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """
    Insert demo feed events for Phase A testing.
    Protected by builder key.
    
    Demo data:
    - SKU123: $100 buy → $155 sell (good spread, should pass)
    - SKU999: $120 buy → $130 sell (bad spread, too small)
    - SKU777: $80 buy → $150 sell (strong spread, should pass)
    """
    test_events = [
        # GOOD SPREAD
        MarketFeedEvent(
            source='manual_buy',
            sku='SKU123',
            title='Test Item A',
            venue='BUY',
            price=100.00,
            currency='CAD',
            url='http://buy.example/itemA'
        ),
        MarketFeedEvent(
            source='manual_sell',
            sku='SKU123',
            title='Test Item A',
            venue='SELL',
            price=155.00,
            currency='CAD',
            url='http://sell.example/itemA'
        ),
        
        # BAD SPREAD
        MarketFeedEvent(
            source='manual_buy',
            sku='SKU999',
            title='Test Item B',
            venue='BUY',
            price=120.00,
            currency='CAD',
            url='http://buy.example/itemB'
        ),
        MarketFeedEvent(
            source='manual_sell',
            sku='SKU999',
            title='Test Item B',
            venue='SELL',
            price=130.00,
            currency='CAD',
            url='http://sell.example/itemB'
        ),
        
        # STRONG SPREAD
        MarketFeedEvent(
            source='manual_buy',
            sku='SKU777',
            title='Test Item C',
            venue='BUY',
            price=80.00,
            currency='CAD',
            url='http://buy.example/itemC'
        ),
        MarketFeedEvent(
            source='manual_sell',
            sku='SKU777',
            title='Test Item C',
            venue='SELL',
            price=150.00,
            currency='CAD',
            url='http://sell.example/itemC'
        ),
    ]
    
    # Check if data already exists
    existing = db.query(MarketFeedEvent).filter(
        MarketFeedEvent.sku.in_(['SKU123', 'SKU999', 'SKU777'])
    ).count()
    
    if existing > 0:
        return {
            "ok": True,
            "message": "Demo data already exists",
            "existing_count": existing,
            "hint": "Run POST /api/arbitrage/scan to process"
        }
    
    try:
        db.add_all(test_events)
        db.commit()
        return {
            "ok": True,
            "inserted": len(test_events),
            "message": "Demo feed events inserted successfully",
            "next_step": "Run POST /api/arbitrage/scan to detect opportunities",
            "expected": {
                "SKU123": "Good spread ($100→$155, net ~$25)",
                "SKU999": "Bad spread ($120→$130, rejected)",
                "SKU777": "Strong spread ($80→$150, net ~$40)",
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
