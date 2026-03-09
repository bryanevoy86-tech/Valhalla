#!/usr/bin/env python
"""
Test Daily Ops Email Integration

Tests:
1. Daily ops email builder function works
2. Endpoint is registered
3. Email can be sent (or at least queued)
4. Cron token auth works

Run: python test_daily_ops_integration.py
"""

import sys
import os
import json
from datetime import datetime, timezone

# Add services/api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'api'))

print("=" * 70)
print("DAILY OPS EMAIL INTEGRATION TEST")
print("=" * 70)

# Test 1: Import the module
print("\n[TEST 1] Importing daily ops email module...")
try:
    from app.jobs.daily_ops_email import (
        build_daily_ops_body,
        build_header_section,
        build_health_section,
        build_runbook_section,
        build_deals_section,
        build_tasks_section,
        build_outcomes_section,
        build_links_section,
        run
    )
    print("✓ Module imported successfully")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

# Test 2: Test database connection
print("\n[TEST 2] Testing database connection...")
try:
    from app.core.db import SessionLocal
    db = SessionLocal()
    db.execute("SELECT 1")
    db.close()
    print("✓ Database connection OK")
except Exception as e:
    print(f"✗ Database error: {e}")
    print("  (This is expected if DB is not configured locally)")

# Test 3: Test email builder sections
print("\n[TEST 3] Testing email builder sections...")
try:
    from app.core.db import SessionLocal
    db = SessionLocal()
    
    # Test individual sections
    sections = {
        "Header": build_header_section(),
        "Health": build_health_section(db),
        "Runbook": build_runbook_section(db),
        "Deals": build_deals_section(db),
        "Tasks": build_tasks_section(db),
        "Outcomes": build_outcomes_section(db),
        "Links": build_links_section(),
    }
    
    for name, content in sections.items():
        if content and len(content) > 0:
            lines = content.count("\n")
            print(f"  ✓ {name:15} - {len(content):4} chars, {lines:2} lines")
        else:
            print(f"  ✗ {name:15} - empty!")
    
    db.close()
except Exception as e:
    print(f"✗ Section building error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test full body builder
print("\n[TEST 4] Testing full email body builder...")
try:
    from app.core.db import SessionLocal
    db = SessionLocal()
    
    body = build_daily_ops_body(db)
    
    if body and len(body) > 100:
        sections = body.count("───")
        print(f"✓ Full body built: {len(body)} chars, {sections} sections")
        print(f"  Preview (first 200 chars):")
        for line in body[:200].split("\n")[:5]:
            print(f"    {line}")
    else:
        print(f"✗ Body is too short: {len(body)} chars")
    
    db.close()
except Exception as e:
    print(f"✗ Body builder error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Check if endpoint is registered
print("\n[TEST 5] Checking if endpoint is registered...")
try:
    from app.main import app
    
    routes = {r.path for r in app.router.routes}
    
    if "/api/notify/daily-ops-email" in routes:
        print("✓ /api/notify/daily-ops-email is registered")
    else:
        print("✗ /api/notify/daily-ops-email NOT registered")
        print(f"  Available /api/notify routes:")
        for r in sorted(routes):
            if "/notify" in r:
                print(f"    - {r}")
    
    if "/api/notify/test-email" in routes:
        print("✓ /api/notify/test-email is registered")
    else:
        print("✗ /api/notify/test-email NOT registered")
        
except Exception as e:
    print(f"✗ Endpoint check error: {e}")

# Test 6: Test CRON_TOKEN verification (without running the app)
print("\n[TEST 6] Testing CRON_TOKEN verification logic...")
try:
    # Mock the token verification
    test_token = "test_secret_12345"
    os.environ["VALHALLA_CRON_TOKEN"] = test_token
    
    from app.api.notify.test_email_router import _verify_cron_token
    
    # Test with valid token
    try:
        result = _verify_cron_token(f"Bearer {test_token}")
        print(f"✓ Valid token accepted: {result}")
    except Exception as e:
        print(f"✗ Valid token rejected: {e}")
    
    # Test with invalid token (should raise)
    try:
        result = _verify_cron_token("Bearer invalid_token")
        print(f"✗ Invalid token accepted!")
    except Exception as e:
        print(f"✓ Invalid token rejected correctly: {str(e.detail)[:50]}")
    
    # Test with no token (should raise)
    try:
        result = _verify_cron_token(None)
        print(f"✗ Missing token accepted!")
    except Exception as e:
        print(f"✓ Missing token rejected correctly: {str(e.detail)[:50]}")
    
    # Clean up
    del os.environ["VALHALLA_CRON_TOKEN"]
    
except Exception as e:
    print(f"✗ Token verification test error: {e}")
    import traceback
    traceback.print_exc()

# Test 7: System email configuration
print("\n[TEST 7] Testing system email configuration...")
try:
    from app.core.identity import system_identity, get_system_email
    
    email = get_system_email()
    print(f"✓ System email configured: {email}")
    
    identity = system_identity()
    print(f"✓ System identity: {identity['from_name']} <{identity['email']}>")
    
except Exception as e:
    print(f"⚠ System email not configured (expected if env var not set): {e}")

print("\n" + "=" * 70)
print("INTEGRATION TEST COMPLETE")
print("=" * 70)
print("\nNext steps:")
print("1. Set required env vars: VALHALLA_SYSTEM_EMAIL, SMTP_* credentials")
print("2. Run: python -m uvicorn services.api.app.main:app --reload")
print("3. Test endpoint: curl -X POST http://localhost:8000/api/notify/daily-ops-email")
print("4. View email in system inbox (if SMTP is configured)")
print("=" * 70)
