#!/usr/bin/env python
"""Create only VA Intake tables directly using SQLAlchemy."""
import os
os.environ["DATABASE_URL"] = "sqlite:///test_direct.db"

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Numeric, Float, func, inspect
from sqlalchemy.orm import declarative_base

# Create a dedicated base for just VA tables
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

# Create engine and tables
engine = create_engine("sqlite:///test_direct.db")
print("Creating VA Intake tables...")
VABase.metadata.create_all(engine)

# Verify
inspector = inspect(engine)
tables = set(inspector.get_table_names())

if 'va_leads' in tables and 'va_approval_queue' in tables:
    print("✅ SUCCESS! VA Intake tables created")
    print(f"Tables: {sorted([t for t in tables if 'va' in t])}")
else:
    print("❌ FAILED! Missing tables")
    print(f"Found: {sorted([t for t in tables if 'va' in t])}")
