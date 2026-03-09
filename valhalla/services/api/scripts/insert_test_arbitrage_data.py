#!/usr/bin/env python3
"""
Insert test arbitrage feed data for Phase A verification.
"""
import os
import sys

# Add services/api to path first
api_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, api_dir)

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import models
from app.models.market_feed_event import MarketFeedEvent
from app.core.db import Base, engine, get_db

# Create session
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# Test data
test_events = [
    # GOOD SPREAD (should create opportunity + sim trade)
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
    
    # BAD SPREAD (should NOT create opportunity - too small)
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
    
    # STRONG SPREAD (should create opportunity + sim trade)
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

try:
    # Insert all
    session.add_all(test_events)
    session.commit()
    print(f"✅ Inserted {len(test_events)} test feed events")
    print("\nTest data inserted:")
    print("  SKU123: $100 buy → $155 sell (good spread)")
    print("  SKU999: $120 buy → $130 sell (bad spread)")
    print("  SKU777: $80 buy → $150 sell (strong spread)")
except Exception as e:
    print(f"❌ Error inserting test data: {e}")
    session.rollback()
finally:
    session.close()
