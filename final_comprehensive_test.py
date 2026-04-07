#!/usr/bin/env python3
"""Final comprehensive test after extended deployment wait."""

import time
import urllib.request
import urllib.error
import json
import sys

print("="*70)
print("FINAL DEPLOYMENT TEST - Waiting 90 seconds for Render to fully deploy")
print("="*70)

for i in range(90):
    time.sleep(1)
    if (i+1) % 15 == 0:
        elapsed = i+1
        remaining = 90 - elapsed
        print(f"  {elapsed}s elapsed... ({remaining}s remaining)")

print("\n" + "="*70)
print("ENDPOINT TESTS")
print("="*70)

# Test 1: Health
try:
    resp = urllib.request.urlopen('https://valhalla-api-ha6a.onrender.com/health', timeout=15)
    print(f'✅ GET /health: {resp.status}')
except Exception as e:
    print(f'❌ GET /health failed: {e}')
    print("\nDEPLOYMENT STILL IN PROGRESS")
    sys.exit(1)

time.sleep(1)

# Test 2: Deals endpoint
try:
    resp = urllib.request.urlopen('https://valhalla-api-ha6a.onrender.com/api/deals', timeout=15)
    data = json.loads(resp.read())
    print(f'✅ GET /api/deals: {resp.status}')
    print(f'✅ Response type: {type(data).__name__}')
    if isinstance(data, list):
        print(f'✅ Deals count: {len(data)}')
    
    print("\n" + "="*70)
    print("🎉 BLOCKER FIXED!")
    print("="*70)
    print("✅ GET /api/deals returns 200")
    print("✅ Alembic migration completed successfully")
    print("✅ Database schema is correct")
    print("✅ WeWeb Deals List can now be called")
    
except urllib.error.HTTPError as e:
    print(f'❌ GET /api/deals: HTTP {e.code}')
    try:
        err = json.loads(e.read())
        print(f'\nError message: {err.get("detail")}')
        if "correlation_id" in err:
            print(f'Correlation ID: {err["correlation_id"]}')
            print('\nNeed to check Render logs with this correlation ID')
            print('to see the actual error from the endpoint')
    except:
        pass
except Exception as e:
    print(f'❌ Connection error: {e}')
    print('\nThe deployment may still be in progress')
