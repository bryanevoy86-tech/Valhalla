#!/usr/bin/env python3
"""
Seed 5 canonical test deals for multi-deal operational verification.

Each deal intentionally in a different realistic state to expose
consistency issues in dashboard, Heimdall, advancement, and audit.
"""

import json
import sys
import os
import sqlite3
from datetime import datetime
from decimal import Decimal

# Load environment
from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault("DATABASE_URL", "sqlite:///valhalla_local.db")
os.environ.setdefault("VALHALLA_JWT_SECRET", "dev-secret-key")


def seed_deals():
    """Create 5 canonical seeded deals in different states using SQL directly."""
    
    conn = sqlite3.connect('valhalla_local.db')
    cursor = conn.cursor()
    
    deals = []
    
    try:
        # First ensure we have leads - check if lead_id=1 exists
        cursor.execute('SELECT id FROM leads WHERE id = 1')
        if not cursor.fetchone():
            # Create a base lead using the actual schema
            cursor.execute('''
                INSERT INTO leads (id, created_at, updated_at, source, lead_name, lead_email, lead_phone, lead_status)
                VALUES (1, datetime('now'), datetime('now'), 'test', 'Test Lead 1', 'lead1@test.local', '555-0001', 'active')
            ''')
        
        # Create additional leads for multi-deal scenario
        for i in range(2, 6):
            cursor.execute(f'''
                INSERT OR IGNORE INTO leads (id, created_at, updated_at, source, lead_name, lead_email, lead_phone, lead_status)
                VALUES ({100+i}, datetime('now'), datetime('now'), 'test', 'Test Lead {i}', 'lead{i}@test.local', '555-000{i}', 'active')
            ''')
        
        conn.commit()
        
        # Clear existing deals 2-14 if they exist
        cursor.execute('DELETE FROM deals WHERE id BETWEEN 10 AND 14')
        conn.commit()
        
        # DEAL A — draft / minimal data (ID 10)
        cursor.execute('''
            INSERT INTO deals (id, created_at, updated_at, lead_id, title, stage, status, arv, notes)
            VALUES (10, datetime('now'), datetime('now'), 1, 'Deal A - Minimal Draft', 'draft', 'active', 250000.00, 'Minimal data - no repairs, offer, contract')
        ''')
        deals.append(("A", 10, "draft", "Minimal Draft"))
        
        # DEAL B — analysis-ready / complete base data (ID 11)
        cursor.execute('''
            INSERT INTO deals (id, created_at, updated_at, lead_id, title, stage, status, arv, estimated_repair_cost, max_allowable_offer, target_assignment_fee, score, notes)
            VALUES (11, datetime('now'), datetime('now'), 102, 'Deal B - Analysis Ready', 'lead_received', 'active', 350000.00, 50000.00, 280000.00, 7000.00, 78.50, 'Complete ARV and repair estimate - ready for analysis')
        ''')
        deals.append(("B", 11, "lead_received", "Analysis Ready"))
        
        # DEAL C — offer-ready / has offer (ID 12)
        cursor.execute('''
            INSERT INTO deals (id, created_at, updated_at, lead_id, title, stage, status, arv, estimated_repair_cost, max_allowable_offer, target_assignment_fee, score, notes)
            VALUES (12, datetime('now'), datetime('now'), 103, 'Deal C - Offer State', 'offer_presented', 'active', 425000.00, 75000.00, 340000.00, 8500.00, 82.25, 'Has offer - ready for contract')
        ''')
        
        # Add offer for deal C
        cursor.execute('''
            INSERT INTO offers (created_at, updated_at, deal_id, offer_price, emd_amount, closing_window_days, generated_by, status)
            VALUES (datetime('now'), datetime('now'), 12, 305000.00, 5000.00, 14, 'system', 'pending')
        ''')
        deals.append(("C", 12, "offer_presented", "Offer State"))
        
        # DEAL D — under-contract / has contract (ID 13)
        cursor.execute('''
            INSERT INTO deals (id, created_at, updated_at, lead_id, title, stage, status, arv, estimated_repair_cost, max_allowable_offer, target_assignment_fee, score, notes)
            VALUES (13, datetime('now'), datetime('now'), 104, 'Deal D - Contract State', 'under_contract', 'active', 520000.00, 120000.00, 400000.00, 10000.00, 86.75, 'Contract signed - in due diligence')
        ''')
        
        # Add offer for deal D first
        cursor.execute('''
            INSERT INTO offers (created_at, updated_at, deal_id, offer_price, emd_amount, closing_window_days, generated_by, status)
            VALUES (datetime('now'), datetime('now'), 13, 385000.00, 10000.00, 21, 'system', 'accepted')
        ''')
        
        # Get the offer ID
        cursor.execute('SELECT id FROM offers WHERE deal_id = 13 ORDER BY id DESC LIMIT 1')
        offer_d_id = cursor.fetchone()[0]
        
        # Add contract for deal D
        cursor.execute(f'''
            INSERT INTO contracts (created_at, updated_at, deal_id, offer_id, status, signing_status)
            VALUES (datetime('now'), datetime('now'), 13, {offer_d_id}, 'active', 'signed')
        ''')
        deals.append(("D", 13, "under_contract", "Contract State"))
        
        # DEAL E — problem deal / blocked state (missing critical piece) (ID 14)
        cursor.execute('''
            INSERT INTO deals (id, created_at, updated_at, lead_id, title, stage, status, arv, max_allowable_offer, score, notes)
            VALUES (14, datetime('now'), datetime('now'), 105, 'Deal E - Blocked Problem Deal', 'lead_received', 'active', 300000.00, 240000.00, 45.00, 'Low score, missing repair estimate - blocked for advancement')
        ''')
        deals.append(("E", 14, "lead_received", "Blocked Problem"))
        
        conn.commit()
        
        print(f"✓ Created {len(deals)} seeded deals\n")
        print("="*80)
        print("SEEDED DEALS SUMMARY")
        print("="*80)
        for letter, deal_id, stage, description in deals:
            print(f"\nDeal {letter} (ID: {deal_id}) — {description}")
            print(f"  Stage: {stage}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error seeding deals: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    success = seed_deals()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    success = seed_deals()
    sys.exit(0 if success else 1)
