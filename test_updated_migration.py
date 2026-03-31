#!/usr/bin/env python3
"""Test if the migration fixed the deals endpoint."""

import time
import urllib.request
import urllib.error
import json

print("Waiting for Render to detect and deploy new commit...")
time.sleep(5)

# Test health first
try:
    resp = urllib.request.urlopen('https://valhalla-api-ha6a.onrender.com/health', timeout=15)
    print(f'✅ GET /health: {resp.status}')
except Exception as e:
    print(f'❌ GET /health: {e}')

print("\nWaiting for full rebuild...")
time.sleep(10)

# Test deals endpoint
try:
    resp = urllib.request.urlopen('https://valhalla-api-ha6a.onrender.com/api/deals?limit=5', timeout=15)
    print(f'✅ GET /api/deals: {resp.status}')
    data = json.loads(resp.read())
    print(f'\nResponse type: {type(data)}')
    if isinstance(data, list):
        print(f'Number of deals: {len(data)}')
        if data:
            print(f'First deal: {json.dumps(data[0], indent=2, default=str)[:500]}...')
        else:
            print('Empty deals list (valid - no deals yet)')
    print("\n🎉 SUCCESS - Endpoint is working!")
except urllib.error.HTTPError as e:
    print(f'❌ GET /api/deals: HTTP {e.code}')
    try:
        err_data = json.loads(e.read())
        print(f'Error: {err_data}')
    except:
        pass
except Exception as e:
    print(f'❌ Error: {type(e).__name__}: {e}')
