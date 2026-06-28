#!/usr/bin/env python
import sqlite3
import os

db = "valhalla_test.db"
if os.path.exists(db):
    conn = sqlite3.connect(db)
    try:
        rows = conn.execute("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 10").fetchall()
        print("Alembic Version Table (last 10 rows):")
        for r in rows:
            print(f"  {r[0]}")
        
        print(f"\nTotal revisions in DB: {len(conn.execute('SELECT COUNT(*) FROM alembic_version').fetchone())}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print("Database doesn't exist yet")
