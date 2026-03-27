#!/usr/bin/env python
"""
Debug Heimdall offer detection
"""

import sys
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///valhalla_local.db")
os.environ.setdefault("VALHALLA_JWT_SECRET", "test_secret_key")

sys.path.insert(0, r'd:\dev\services\api')

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, text
from app.models.deal import Deal

# Setup DB connection
engine = create_engine("sqlite:///valhalla_local.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("\n" + "="*80)
print("DEBUG: HEIMDALL OFFER DETECTION")
print("="*80)

deal_id = 11

# Get deal
deal = db.query(Deal).filter(Deal.id == deal_id).first()
print(f"\nDeal 11:")
print(f"  ID: {deal.id}")
print(f"  Stage: {deal.stage}")
print(f"  ARV: {deal.arv}")
print(f"  Repairs: {deal.estimated_repair_cost}")

# Try offer query with raw SQL
print(f"\nQuerying offers with raw SQL:")
try:
    offer_row = db.execute(
        text("SELECT id, deal_id, offer_price, status FROM offers WHERE deal_id = ? LIMIT 1"),
        [deal_id]
    ).first()
    if offer_row:
        print(f"  Found offer: ID={offer_row[0]}, deal_id={offer_row[1]}, price={offer_row[2]}, status={offer_row[3]}")
    else:
        print(f"  No offer found")
except Exception as e:
    print(f"  Error: {e}")

# Now run Heimdall analyze
print(f"\nRunning Heimdall analyze...")
from app.services.heimdall_service import analyze_deal

analysis = analyze_deal(deal_id, db)
print(f"Current stage: {analysis.current_stage}")
print(f"Blockers: {analysis.blocker_flags}")
print(f"Recommended: {analysis.recommended_stage}")
print(f"Can advance: {analysis.can_advance}")

db.close()
print()
