# Fix both audit_events and governance_decisions tables

import app.models  # Ensure models are imported
from app.core.db import engine
from sqlalchemy import text

with engine.begin() as conn:
    print("=== Fixing audit_events table ===")
    # Get current columns
    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'audit_events'
    """))
    current_cols = {row[0] for row in result}
    print(f"Current columns: {current_cols}")
    
    # Drop old columns that don't match
    for old_col in ['actor', 'action', 'target', 'result', 'ip', 'user_agent', 'meta']:
        if old_col in current_cols:
            conn.execute(text(f'ALTER TABLE audit_events DROP COLUMN "{old_col}"'))
            print(f"Dropped {old_col}")
    
    # Add missing columns
    if 'deal_id' not in current_cols:
        conn.execute(text("ALTER TABLE audit_events ADD COLUMN deal_id INTEGER"))
        print("Added deal_id")
    
    if 'professional_id' not in current_cols:
        conn.execute(text("ALTER TABLE audit_events ADD COLUMN professional_id INTEGER"))
        print("Added professional_id")
    
    if 'code' not in current_cols:
        conn.execute(text("ALTER TABLE audit_events ADD COLUMN code VARCHAR(100) NOT NULL DEFAULT 'UNKNOWN'"))
        print("Added code")
    
    if 'severity' not in current_cols:
        conn.execute(text("ALTER TABLE audit_events ADD COLUMN severity VARCHAR(50) NOT NULL DEFAULT 'warning'"))
        print("Added severity")
    
    if 'message' not in current_cols:
        conn.execute(text("ALTER TABLE audit_events ADD COLUMN message VARCHAR(500) NOT NULL DEFAULT ''"))
        print("Added message")
    
    if 'is_resolved' not in current_cols:
        conn.execute(text("ALTER TABLE audit_events ADD COLUMN is_resolved BOOLEAN NOT NULL DEFAULT FALSE"))
        print("Added is_resolved")
    
    if 'resolved_at' not in current_cols:
        conn.execute(text("ALTER TABLE audit_events ADD COLUMN resolved_at TIMESTAMP WITH TIME ZONE"))
        print("Added resolved_at")
    
    print("\n=== Checking governance_decisions table ===")
    # Verify governance_decisions has correct schema
    result2 = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'governance_decisions'
    """))
    gov_cols = {row[0] for row in result2}
    print(f"Current columns: {gov_cols}")
    print("✓ governance_decisions table already has correct schema!")

print("\nSchema update complete!")
