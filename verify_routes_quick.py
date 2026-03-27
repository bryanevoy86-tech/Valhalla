#!/usr/bin/env python3
"""
Quick verification script - test the fixed routes post-startup
"""
import sys
import os
from pathlib import Path

# Add services/api to path
sys.path.insert(0, str(Path(__file__).parent / "services" / "api"))

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Now import app
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

print("="*80)
print("LIVE API VERIFICATION - POST FIX")
print("="*80)

routes_to_check = [
    ("GET", "/health", None, "System health check"),
    ("POST", "/api/heimdall/deals/1/analyze", None, "Heimdall analyze endpoint"),
    ("POST", "/api/heimdall/deals/1/advance-stage", {"requested_stage": "lead_received", "approved_by": "test", "reason": "test"}, "Heimdall advance-stage endpoint"),
    ("GET", "/api/audit/deals/1", None, "Audit deals endpoint"),
    ("GET", "/api/audit", None, "Audit base endpoint"),
    ("GET", "/api/dashboard/pipeline", None, "Dashboard pipeline endpoint"),
]

passed = []
failed = []
errors = []

for method, path, body, description in routes_to_check:
    try:
        if method == "GET":
            resp = client.get(path)
        elif method == "POST":
            resp = client.post(path, json=body or {})
        else:
            resp = None
            
        status = resp.status_code if resp else "ERROR"
        
        # Check if route exists (not 404)
        if status == 404:
            print(f"❌ {method:4} {path:45} → 404 (NOT FOUND)")
            failed.append((method, path, description))
        elif status >= 500:
            print(f"⚠️  {method:4} {path:45} → {status} (SERVER ERROR)")
            errors.append((method, path, description, status))
        else:
            print(f"✅ {method:4} {path:45} → {status}")
            passed.append((method, path, description))
    except Exception as e:
        print(f"❌ {method:4} {path:45} → ERROR: {type(e).__name__}")
        errors.append((method, path, description, str(e)))

print("="*80)
print(f"RESULTS: {len(passed)} live | {len(failed)} not-found | {len(errors)} errors")
print("="*80)

if passed:
    print("\n✅ LIVE ROUTES:")
    for method, path, desc in passed:
        print(f"   {method:4} {path:45} - {desc}")

if failed:
    print("\n❌ NOT FOUND (404 - ROUTE MISSING):")
    for method, path, desc in failed:
        print(f"   {method:4} {path:45} - {desc}")

if errors:
    print("\n⚠️  ERRORS:")
    for method, path, desc, err in errors:
        print(f"   {method:4} {path:45} - {desc} ({err})")

sys.exit(0 if len(failed) == 0 else 1)
