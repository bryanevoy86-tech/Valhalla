#!/usr/bin/env python
"""
Database bootstrap script for Sprint 2.

This script initializes a fresh database with the core pipeline schema
without depending on the potentially broken alembic migration chain.

Usage:
    python db_bootstrap.py
"""
import os
import sys
from pathlib import Path

# Configure environment
os.environ.setdefault('DATABASE_URL', 'sqlite:///./valhalla_local.db')
os.environ.setdefault('VALHALLA_JWT_SECRET', 'dev-secret-key')

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(PROJECT_ROOT))

# Set up module aliasing
from importlib import import_module
if 'app' not in sys.modules:
    sys.modules['app'] = import_module('services.api.app')
    print("✅ Module aliasing configured: app -> services.api.app")

# Now import SQLAlchemy
from sqlalchemy import create_engine, text, inspect
from sqlalchemy import DateTime, Integer, String, Numeric, Text, Boolean, JSON, ForeignKey
from sqlalchemy import MetaData, Table, Column, func

print("=" * 80)
print("DATABASE BOOTSTRAP SCRIPT FOR SPRINT 2")
print("=" * 80)

# Check if database already exists
db_url = os.getenv('DATABASE_URL', '')
if db_url.startswith('sqlite'):
    db_path = Path(db_url.replace('sqlite:///', ''))
    if db_path.exists() and db_path.stat().st_size > 0:
        print(f"\n⚠️  Database already exists: {db_path}")
        response = input("Do you want to drop and recreate it? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Bootstrap cancelled.")
            sys.exit(1)
        db_path.unlink()
        print("Existing database removed.")

# Create engine
engine = create_engine(db_url, echo=False)

print("\n📦 Creating core pipeline tables...")

# Create tables using raw SQL DDL
with engine.connect() as conn:
    # Leads table
    conn.execute(text("""
        CREATE TABLE leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            source VARCHAR(255),
            lead_name VARCHAR(255),
            lead_email VARCHAR(255),
            lead_phone VARCHAR(20),
            property_address VARCHAR(512),
            property_city VARCHAR(255),
            property_state VARCHAR(2),
            property_zip VARCHAR(10),
            estimated_arv DECIMAL(15, 2),
            lead_status VARCHAR(50) NOT NULL DEFAULT 'new',
            notes TEXT
        )
    """))
    print("  ✅ leads table created")
    
    # Deals table
    conn.execute(text("""
        CREATE TABLE deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            lead_id INTEGER NOT NULL,
            title VARCHAR(255) NOT NULL,
            stage VARCHAR(50) NOT NULL DEFAULT 'lead_received',
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            arv DECIMAL(15, 2),
            estimated_repair_cost DECIMAL(15, 2),
            max_allowable_offer DECIMAL(15, 2),
            target_assignment_fee DECIMAL(15, 2),
            score DECIMAL(8, 2) DEFAULT 0,
            notes TEXT,
            disposition_status VARCHAR(50),
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """))
    print("  ✅ deals table created")
    
    # Offers table
    conn.execute(text("""
        CREATE TABLE offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            deal_id INTEGER NOT NULL,
            offer_price DECIMAL(15, 2) NOT NULL,
            emd_amount DECIMAL(15, 2),
            closing_window_days INTEGER,
            conditions_summary TEXT,
            generated_by VARCHAR(255),
            status VARCHAR(50) NOT NULL DEFAULT 'draft',
            FOREIGN KEY (deal_id) REFERENCES deals(id)
        )
    """))
    print("  ✅ offers table created")
    
    # Buyers table
    conn.execute(text("""
        CREATE TABLE buyers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            phone VARCHAR(20),
            buy_box_json JSON,
            preferred_markets VARCHAR(255),
            cash_ready BOOLEAN DEFAULT 0,
            notes TEXT,
            status VARCHAR(50) NOT NULL DEFAULT 'active'
        )
    """))
    print("  ✅ buyers table created")
    
    # Contracts table
    conn.execute(text("""
        CREATE TABLE contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            deal_id INTEGER,
            offer_id INTEGER,
            status VARCHAR(50) NOT NULL DEFAULT 'draft',
            template_id VARCHAR(255),
            content TEXT,
            pdf_url VARCHAR(512),
            signing_status VARCHAR(50),
            docusign_id VARCHAR(255),
            FOREIGN KEY (deal_id) REFERENCES deals(id),
            FOREIGN KEY (offer_id) REFERENCES offers(id)
        )
    """))
    print("  ✅ contracts table created")
    
    # Audit logs table
    conn.execute(text("""
        CREATE TABLE audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            entity_type VARCHAR(50) NOT NULL,
            entity_id INTEGER NOT NULL,
            action VARCHAR(100) NOT NULL,
            previous_value JSON,
            new_value JSON,
            user_id VARCHAR(255),
            notes TEXT
        )
    """))
    print("  ✅ audit_logs table created")
    
    # Buyer matches table
    conn.execute(text("""
        CREATE TABLE buyer_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            deal_id INTEGER NOT NULL,
            buyer_id INTEGER NOT NULL,
            match_score DECIMAL(8, 2),
            match_reason TEXT,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            FOREIGN KEY (deal_id) REFERENCES deals(id),
            FOREIGN KEY (buyer_id) REFERENCES buyers(id)
        )
    """))
    print("  ✅ buyer_matches table created")
    
    # Deal stage history table
    conn.execute(text("""
        CREATE TABLE deal_stage_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            deal_id INTEGER NOT NULL,
            old_stage VARCHAR(50),
            new_stage VARCHAR(50) NOT NULL,
            override_reason TEXT,
            user_id VARCHAR(255),
            FOREIGN KEY (deal_id) REFERENCES deals(id)
        )
    """))
    print("  ✅ deal_stage_history table created")
    
    conn.commit()

# Verify database
print("\n✅ Verifying database...")
inspector = inspect(engine)
actual_tables = inspector.get_table_names()
print(f"✅ Database verified: {len(actual_tables)} tables present")
for table_name in sorted(actual_tables):
    print(f"   - {table_name}")

print("\n" + "=" * 80)
print("✅ DATABASE BOOTSTRAP COMPLETE")
print("=" * 80)
print("\n Ready for Sprint 2 core pipeline development!")
print("=" * 80)

