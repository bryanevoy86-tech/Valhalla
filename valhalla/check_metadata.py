#!/usr/bin/env python
"""Check system_metadata table status and update backend_complete."""

import sqlite3
from datetime import datetime

DB_PATH = "valhalla.db"

def create_system_metadata_table():
    """Create the system_metadata table if it doesn't exist."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create the table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_metadata (
            id INTEGER PRIMARY KEY NOT NULL,
            version VARCHAR NOT NULL DEFAULT '1.0.0',
            backend_complete BOOLEAN NOT NULL DEFAULT 0,
            notes VARCHAR,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME
        )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_system_metadata_id ON system_metadata(id)")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

def check_and_update_metadata():
    """Check and update system_metadata."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # First, check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print("Available tables:", tables)
        
        if "system_metadata" not in tables:
            print("\n⚠️  system_metadata table does not exist. Creating...")
            conn.close()
            if not create_system_metadata_table():
                return False
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
        
        # Step 1: Verify the metadata row
        print("\n=== Step 1: Verify metadata row ===")
        cursor.execute(
            "SELECT id, version, backend_complete, notes, updated_at, completed_at "
            "FROM system_metadata ORDER BY updated_at DESC LIMIT 5"
        )
        rows = cursor.fetchall()
        
        if not rows:
            print("❌ No rows found in system_metadata table!")
            print("Creating initial row with id=1...")
            
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO system_metadata (id, version, backend_complete, notes, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (1, "1.0.0", 0, "System metadata initialized.", now)
            )
            conn.commit()
            
            # Fetch again
            cursor.execute(
                "SELECT id, version, backend_complete, notes, updated_at, completed_at "
                "FROM system_metadata ORDER BY updated_at DESC LIMIT 5"
            )
            rows = cursor.fetchall()
        
        print(f"Found {len(rows)} row(s):")
        for row in rows:
            print(f"  ID: {row[0]}, Version: {row[1]}, Backend Complete: {row[2]}, "
                  f"Updated: {row[4]}, Completed: {row[5]}")
        
        # Get the first (most recent) row
        metadata_id = rows[0][0]
        print(f"\nUsing row with id = {metadata_id}")
        
        # Step 2: Mark backend complete
        print("\n=== Step 2: Mark backend_complete = TRUE ===")
        now = datetime.now().isoformat()
        
        cursor.execute(
            "UPDATE system_metadata "
            "SET backend_complete = 1, "
            "    completed_at = ?, "
            "    updated_at = ?, "
            "    notes = COALESCE(notes, '') || char(10) || 'Marked backend_complete TRUE on ' || ? "
            "WHERE id = ?",
            (now, now, now, metadata_id)
        )
        
        conn.commit()
        print(f"✅ Updated row id={metadata_id} successfully!")
        
        # Verify the update
        cursor.execute(
            "SELECT id, version, backend_complete, notes, updated_at, completed_at "
            "FROM system_metadata WHERE id = ?",
            (metadata_id,)
        )
        updated_row = cursor.fetchone()
        print(f"\nUpdated row: {updated_row}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = check_and_update_metadata()
    exit(0 if success else 1)
