#!/usr/bin/env python
"""Test VA Intake fix - verify endpoints work with tables created."""
import os
import subprocess
import sys

os.environ["DATABASE_URL"] = "sqlite:///va_test.db"

# Step 1: Create tables directly using SQLAlchemy  
print("Step 1: Creating VA Intake tables...")
try:
    from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Numeric, Float, func, inspect
    from sqlalchemy.orm import declarative_base
    
    VABase = declarative_base()
    
    class VALead(VABase):
        __tablename__ = "va_leads"
        id = Column(Integer, primary_key=True, index=True)
        source_platform = Column(String(60), nullable=False)
        source_type = Column(String(60), nullable=False)
        source_url = Column(String(500), nullable=True)
        address = Column(String(240), nullable=True)
        city = Column(String(120), nullable=True)
        province = Column(String(10), nullable=True)
        seller_name = Column(String(160), nullable=True)
        seller_phone = Column(String(40), nullable=True)
        seller_email = Column(String(160), nullable=True)
        asking_price = Column(Numeric(15, 2), nullable=True)
        raw_text = Column(Text(), nullable=True)
        va_notes = Column(Text(), nullable=True)
        strategy_fit = Column(String(60), nullable=True)
        submitted_by = Column(String(80), nullable=False, server_default="va")
        heimdall_score = Column(Integer, nullable=False, server_default="0")
        risk_level = Column(String(20), nullable=False, server_default="high")
        confidence = Column(Float, nullable=False, server_default="0.0")
        recommended_action = Column(String(255), nullable=True)
        status = Column(String(60), nullable=False, server_default="pending")
        stage = Column(String(60), nullable=False, server_default="intake")
        deal_id = Column(Integer, nullable=True, index=True)
        created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
        updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
        approved_at = Column(DateTime(timezone=True), nullable=True)
        converted_at = Column(DateTime(timezone=True), nullable=True)
    
    class VAApprovalQueue(VABase):
        __tablename__ = "va_approval_queue"
        id = Column(Integer, primary_key=True, index=True)
        entity_type = Column(String(60), nullable=False, server_default="lead")
        entity_id = Column(Integer, nullable=False, index=True)
        va_lead_id = Column(Integer, nullable=False, index=True)
        status = Column(String(60), nullable=False, server_default="pending")
        recommended_action = Column(String(255), nullable=True)
        heimdall_score = Column(Integer, nullable=True)
        risk_level = Column(String(20), nullable=True)
        assigned_to = Column(String(80), nullable=True)
        approved_by = Column(String(80), nullable=True)
        approved_at = Column(DateTime(timezone=True), nullable=True)
        denied_by = Column(String(80), nullable=True)
        denied_at = Column(DateTime(timezone=True), nullable=True)
        denial_reason = Column(Text(), nullable=True)
        created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
        updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    engine = create_engine("sqlite:///va_test.db")
    VABase.metadata.create_all(engine)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    
    if 'va_leads' in tables and 'va_approval_queue' in tables:
        print("✅ Tables created successfully")
    else:
        print(f"❌ Failed to create tables. Found: {sorted([t for t in tables if 'va' in t])}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Error creating tables: {e}")
    sys.exit(1)

# Step 2: Test endpoints
print("\nStep 2: Testing endpoints with TestClient...")
try:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    
    # Test GET /api/va-intake/leads
    resp1 = client.get("/api/va-intake/leads")
    print(f"GET /api/va-intake/leads: {resp1.status_code}")
    if resp1.status_code != 200:
        print(f"  Error: {resp1.text[:150]}")
    
    # Test GET /api/va-intake/approvals/pending
    resp2 = client.get("/api/va-intake/approvals/pending")
    print(f"GET /api/va-intake/approvals/pending: {resp2.status_code}")
    if resp2.status_code != 200:
        print(f"  Error: {resp2.text[:150]}")
    
    if resp1.status_code == 200 and resp2.status_code == 200:
        print("\n✅ SUCCESS! Both endpoints return 200")
        sys.exit(0)
    else:
        print("\n❌ FAILED! One or more endpoints returned non-200")
        sys.exit(1)
        
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
