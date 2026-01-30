#!/usr/bin/env python3
"""
VALHALLA GO-LIVE SAFETY FIX - Phase 1
Sets backend_complete = TRUE in database (root blocker)

Usage:
  1. Ensure you have DATABASE_URL set in your environment
  2. Run: python fix_backend_complete.py
  3. Check output - should show backend_complete = True
  4. Then: python ops_report.py (to verify governance passes)
"""

import os
import sys
from datetime import datetime

# Import from your app
try:
    from services.api.app.database import SessionLocal
    from services.api.app.models.system_metadata import SystemMetadata
except ImportError:
    print("[ERROR] Cannot import app modules. Are you in the valhalla directory?")
    print("        Try: cd c:\\dev\\valhalla")
    sys.exit(1)


def fix_backend_complete():
    """Set backend_complete = TRUE in system_metadata table."""
    
    print("\n" + "="*60)
    print("VALHALLA GO-LIVE SAFETY FIX - Phase 1")
    print("Setting backend_complete = TRUE")
    print("="*60 + "\n")
    
    # Verify DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("[WARNING] DATABASE_URL not set in environment")
        print("          Using default connection from app.database")
    else:
        print(f"[OK] Using DATABASE_URL: {db_url[:50]}...")
    
    try:
        db = SessionLocal()
        
        # Check current state
        print("\n[STEP 1] Checking current system_metadata...")
        current = db.query(SystemMetadata).filter(SystemMetadata.id == 1).first()
        
        if current:
            print(f"  Found existing row:")
            print(f"    - id: {current.id}")
            print(f"    - version: {current.version}")
            print(f"    - backend_complete: {current.backend_complete}")
            print(f"    - updated_at: {current.updated_at}")
            print(f"    - completed_at: {current.completed_at}")
        else:
            print("  No existing row found (will create)")
        
        # Update or create
        print("\n[STEP 2] Setting backend_complete = TRUE...")
        
        if current:
            current.backend_complete = True
            current.notes = "Go-live backend marked complete"
            current.updated_at = datetime.utcnow()
            current.completed_at = datetime.utcnow()
        else:
            current = SystemMetadata(
                id=1,
                version="1.0.0",
                backend_complete=True,
                notes="Go-live backend marked complete",
                completed_at=datetime.utcnow(),
            )
            db.add(current)
        
        db.commit()
        db.refresh(current)
        
        print(f"  ✅ Updated:")
        print(f"    - backend_complete: {current.backend_complete}")
        print(f"    - updated_at: {current.updated_at}")
        print(f"    - completed_at: {current.completed_at}")
        
        # Verify
        print("\n[STEP 3] Verifying change...")
        verified = db.query(SystemMetadata).filter(SystemMetadata.id == 1).first()
        if verified and verified.backend_complete:
            print(f"  ✅ Verified: backend_complete = {verified.backend_complete}")
            print("\n" + "="*60)
            print("SUCCESS")
            print("="*60)
            print("\nNext steps:")
            print("  1. Redeploy FastAPI to Render:")
            print("     git add services/api/main.py")
            print("     git commit -m 'Fix: Add /governance endpoint'")
            print("     git push")
            print("\n  2. Wait 2-3 min for Render deployment")
            print("\n  3. Verify governance passes:")
            print("     python ops_report.py")
            print("\n" + "="*60 + "\n")
            return 0
        else:
            print("  ❌ Verification failed!")
            return 1
            
    except Exception as e:
        print(f"\n[FATAL] {e}")
        import traceback
        traceback.print_exc()
        return 2
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(fix_backend_complete())
