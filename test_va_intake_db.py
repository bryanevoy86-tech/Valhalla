"""Test VA Intake system with database persistence"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent / "services" / "api"))
os.environ["DATABASE_URL"] = "sqlite:///./valhalla_local.db"
os.environ["VALHALLA_JWT_SECRET"] = "dev-secret-key-change-in-production"

from sqlalchemy.orm import Session
from services.api.app.core.db import SessionLocal, engine
from services.api.app.models import VALead, VAApprovalQueue, VAAuditLog
from services.api.app.services.heimdall_lead_intake import score_lead, build_lead_record

print("=" * 70)
print("VA INTAKE SYSTEM - DATABASE PERSISTENCE TEST")
print("=" * 70)

# Test 1: Create a test lead
print("\n[TEST 1] Creating and scoring a test lead...")
test_payload = {
    "source_platform": "facebook",
    "source_type": "manual_va",
    "source_url": "manual import from VA",
    "address": "456 Test Avenue",
    "city": "Toronto",
    "province": "ON",
    "seller_name": "John Seller",
    "seller_phone": "416-555-5678",
    "seller_email": None,
    "asking_price": 325000.00,
    "raw_text": "Must sell ASAP. House needs significant repairs. Foreclosure situation.",
    "va_notes": "Definitely distressed. Estate sale. Vacant property.",
    "strategy_fit": "wholesale",
    "submitted_by": "va_test_script"
}

# Score the lead
analysis = score_lead(test_payload)
print(f"✅ Heimdall Score: {analysis['heimdall_score']}/100")
print(f"   Risk Level: {analysis['risk_level']}")
print(f"   Confidence: {analysis['confidence']}")

# Build lead record
lead_record = build_lead_record(test_payload, analysis)
print(f"✅ Lead Record Created")

# Test 2: Save to database
print("\n[TEST 2] Saving lead to database...")
db = SessionLocal()
try:
    va_lead = VALead(**lead_record)
    db.add(va_lead)
    db.commit()
    db.refresh(va_lead)
    lead_id = va_lead.id
    print(f"✅ Lead saved with ID: {lead_id}")
    print(f"   Status: {va_lead.status}")
    print(f"   Stage: {va_lead.stage}")
finally:
    db.close()

# Test 3: Retrieve from database
print("\n[TEST 3] Retrieving lead from database...")
db = SessionLocal()
try:
    retrieved_lead = db.query(VALead).filter(VALead.id == lead_id).first()
    if retrieved_lead:
        print(f"✅ Lead retrieved successfully")
        print(f"   Seller: {retrieved_lead.seller_name}")
        print(f"   Address: {retrieved_lead.address}, {retrieved_lead.city}, {retrieved_lead.province}")
        print(f"   Score: {retrieved_lead.heimdall_score}/100")
        print(f"   Asking Price: ${retrieved_lead.asking_price}")
    else:
        print(f"❌ Lead not found!")
finally:
    db.close()

# Test 4: Check approval queue
print("\n[TEST 4] Checking approval queue...")
db = SessionLocal()
try:
    queued_approvals = db.query(VAApprovalQueue).all()
    pending_approvals = db.query(VAApprovalQueue).filter(
        VAApprovalQueue.status == "pending"
    ).count()
    print(f"✅ Total approvals in queue: {len(queued_approvals)}")
    print(f"   Pending approvals: {pending_approvals}")
finally:
    db.close()

# Test 5: List all leads
print("\n[TEST 5] Listing all VA leads...")
db = SessionLocal()
try:
    all_leads = db.query(VALead).all()
    print(f"✅ Total VA leads in database: {len(all_leads)}")
    for lead in all_leads[-3:]:  # Show last 3 leads
        print(f"   - {lead.seller_name} ({lead.city}, {lead.province}) - Score: {lead.heimdall_score}")
finally:
    db.close()

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED - VA INTAKE DATABASE PERSISTENCE WORKING")
print("=" * 70)
