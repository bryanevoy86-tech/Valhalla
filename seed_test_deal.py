#!/usr/bin/env python
"""Seed a canonical test deal for workflow verification."""

import sqlite3
from datetime import datetime, UTC

conn = sqlite3.connect('valhalla_local.db')
cursor = conn.cursor()

# First create a lead if one doesn't exist
cursor.execute("SELECT COUNT(*) FROM leads")
if cursor.fetchone()[0] == 0:
    cursor.execute("""
        INSERT INTO leads (lead_name, lead_email, lead_phone, source, property_address, 
                          property_city, property_state, lead_status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ("Test Lead", "test@workflow.local", "555-0001", "seeded", 
          "123 Test St", "Denver", "CO", "active",
          datetime.now(UTC).isoformat(), datetime.now(UTC).isoformat()))
    conn.commit()
    print("✓ Created test lead")

# Get the lead ID
cursor.execute("SELECT id FROM leads ORDER BY id DESC LIMIT 1")
lead_id = cursor.fetchone()[0]
print(f"✓ Using lead ID: {lead_id}")

# Create a canonical test deal
cursor.execute("""
    INSERT INTO deals 
    (lead_id, title, stage, status, arv, estimated_repair_cost, 
     max_allowable_offer, target_assignment_fee, score, notes, disposition_status,
     created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    lead_id,                              # lead_id
    "Test Deal - Workflow Verification",  # title
    "draft",                              # stage
    "active",                             # status
    350000.00,                            # arv
    50000.00,                             # estimated_repair_cost
    280000.00,                            # max_allowable_offer
    7000.00,                              # target_assignment_fee
    75.5,                                 # score (Heimdall score)
    "Seeded for workflow verification",   # notes
    "active",                             # disposition_status
    datetime.now(UTC).isoformat(),        # created_at
    datetime.now(UTC).isoformat()         # updated_at
))

conn.commit()

# Get the deal ID
cursor.execute("SELECT id FROM deals ORDER BY id DESC LIMIT 1")
deal_id = cursor.fetchone()[0]

print(f"✓ Created test deal ID: {deal_id}")

# Verify
cursor.execute("""
    SELECT id, lead_id, title, stage, status, score 
    FROM deals WHERE id = ?
""", (deal_id,))
row = cursor.fetchone()
if row:
    print(f"\n✓ SEEDED DEAL READY")
    print(f"  ID: {row[0]}")
    print(f"  Lead: {row[1]}")
    print(f"  Title: {row[2]}")
    print(f"  Stage: {row[3]}")
    print(f"  Status: {row[4]}")
    print(f"  Score: {row[5]}")
    print(f"\nUse deal_id={deal_id} for verification flow")
else:
    print("✗ Failed to create deal")

conn.close()
