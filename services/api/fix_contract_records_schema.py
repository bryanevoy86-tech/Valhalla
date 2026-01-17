# Fix contract_records table schema directly

import app.models  # Ensure models are imported
from app.core.db import engine
from sqlalchemy import text

with engine.begin() as conn:
    # Get current columns
    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'contract_records'
    """))
    current_cols = {row[0] for row in result}
    print(f"Current columns: {current_cols}")
    
    # Add missing columns
    if 'deal_id' not in current_cols:
        conn.execute(text("ALTER TABLE contract_records ADD COLUMN deal_id INTEGER NOT NULL DEFAULT 0"))
        print("Added deal_id")
    
    if 'professional_id' not in current_cols:
        conn.execute(text("ALTER TABLE contract_records ADD COLUMN professional_id INTEGER"))
        print("Added professional_id")
    
    if 'status' not in current_cols:
        conn.execute(text("ALTER TABLE contract_records ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'draft'"))
        print("Added status")
    
    if 'version' not in current_cols:
        conn.execute(text("ALTER TABLE contract_records ADD COLUMN version INTEGER NOT NULL DEFAULT 1"))
        print("Added version")
    
    if 'title' not in current_cols:
        conn.execute(text("ALTER TABLE contract_records ADD COLUMN title VARCHAR(200) NOT NULL DEFAULT 'Untitled'"))
        print("Added title")
    
    if 'storage_url' not in current_cols:
        conn.execute(text("ALTER TABLE contract_records ADD COLUMN storage_url VARCHAR(500)"))
        print("Added storage_url")
    
    if 'updated_at' not in current_cols:
        conn.execute(text("ALTER TABLE contract_records ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()"))
        print("Added updated_at")
    
    if 'signed_at' not in current_cols:
        conn.execute(text("ALTER TABLE contract_records ADD COLUMN signed_at TIMESTAMP WITH TIME ZONE"))
        print("Added signed_at")
    
    # Drop old columns that don't match the schema
    if 'template_id' in current_cols:
        conn.execute(text("ALTER TABLE contract_records DROP COLUMN template_id"))
        print("Dropped template_id")
    
    if 'filename' in current_cols:
        conn.execute(text("ALTER TABLE contract_records DROP COLUMN filename"))
        print("Dropped filename")
    
    if 'context_json' in current_cols:
        conn.execute(text("ALTER TABLE contract_records DROP COLUMN context_json"))
        print("Dropped context_json")

print("\nSchema update complete!")
