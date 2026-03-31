#!/usr/bin/env python3
"""Test if production has the latest deployment."""

import urllib.request
import urllib.error
import json
import time

print("Testing production deployment...")
print()

# Test health endpoint
try:
    resp = urllib.request.urlopen('https://valhalla-api-ha6a.onrender.com/health', timeout=10)
    print(f"✅ GET /health: {resp.status}")
except Exception as e:
    print(f"❌ GET /health error: {e}")

time.sleep(1)

# Test deals endpoint
print("\nTesting GET /api/deals...")
try:
    resp = urllib.request.urlopen('https://valhalla-api-ha6a.onrender.com/api/deals', timeout=10)
    print(f"✅ GET /api/deals: {resp.status}")
    print("SUCCESS - Fix has been deployed!\n")
except urllib.error.HTTPError as e:
    print(f"❌ GET /api/deals: HTTP {e.code}")
    try:
        body = e.read().decode()
        err_json = json.loads(body)
        print(f"Correlation ID: {err_json.get('correlation_id', 'unknown')}")
        print(f"Detail: {err_json.get('detail', 'No detail')}")
    except:
        pass
except Exception as e:
    print(f"❌ Error: {e}")
