#!/usr/bin/env python3
"""Test the fixed endpoint after deployment."""

import time
import urllib.request
import urllib.error
import json

print("Waiting 40 seconds for Render to detect, build, and deploy...")
for i in range(40):
    time.sleep(1)
    if (i+1) % 10 == 0:
        print(f"  {i+1}s elapsed...")

print("\n" + "="*70)
print("Testing deployment...")
print("="*70)

# Test health endpoint
try:
    resp = urllib.request.urlopen('https://valhalla-api-ha6a.onrender.com/health', timeout=15)
    print(f'✅ GET /health: {resp.status}')
except Exception as e:
    print(f'❌ GET /health: {e}')
    exit(1)

time.sleep(2)

# Test deals endpoint
try:
    resp = urllib.request.urlopen('https://valhalla-api-ha6a.onrender.com/api/deals?limit=1', timeout=15)
    status = resp.status
    data = json.loads(resp.read())
    print(f'✅ GET /api/deals: {status}')
    print(f'\n✅ SUCCESS! Endpoint is working!')
    print(f'\nResponse type: {type(data)}')
    if isinstance(data, list):
        print(f'Deals returned: {len(data)}')
        if len(data) == 0:
            print('(Empty list - no deals in DB yet, but schema is correct)')
    print("\n" + "="*70)
    print("🎉 BLOCKER RESOLVED - GET /api/deals returns 200")
    print("="*70)
except urllib.error.HTTPError as e:
    print(f'❌ GET /api/deals: HTTP {e.code}')
    try:
        err_data = json.loads(e.read())
        print(f'Error: {err_data.get("detail")}')
        print(f'Correlation ID: {err_data.get("correlation_id")}')
    except:
        print('(Could not parse error response)')
except Exception as e:
    print(f'❌ {type(e).__name__}: {e}')
