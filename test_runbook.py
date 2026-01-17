#!/usr/bin/env python
"""
Standalone test of runbook function without full app initialization.
"""
import sys
import os

# Add the services/api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'api'))

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create in-memory SQLite database for testing
engine = create_engine('sqlite:///:memory:')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Now test build_runbook with empty database
try:
    from app.services.runbook import build_runbook
    result = build_runbook(db)
    print("SUCCESS: build_runbook() executed without crash")
    print(f"Blockers: {len(result['blockers'])}")
    print(f"Warnings: {len(result['warnings'])}")
    print(f"Info: {len(result['info'])}")
    print(f"OK to enable: {result['ok_to_enable_go_live']}")
    print("\nFull result:")
    import json
    print(json.dumps(result, indent=2, default=str))
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
