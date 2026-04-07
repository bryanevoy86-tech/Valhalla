#!/usr/bin/env python
"""Test production endpoints after lead_id fix deployment."""
import urllib.request
import json
import time
import sys

BASE_URL = "https://valhalla-api-ha6a.onrender.com"

def test_endpoint(method, path):
    """Test an endpoint and return status code and body."""
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            status = response.status
            body = response.read().decode('utf-8')
            headers = dict(response.headers)
            return status, headers, body
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode('utf-8')

print("=" * 80)
print("TESTING ENDPOINTS AFTER LEAD_ID FIX")
print("=" * 80)
print(f"Base URL: {BASE_URL}")
print()

# Test /health
print("1. Testing GET /health")
status, headers, body = test_endpoint("GET", "/health")
print(f"   Status: {status}")
if status == 200:
    print("   ✅ PASS")
else:
    print("   ❌ FAIL")
    print(f"   Body: {body[:200]}")
print()

# Test /api/deals - the critical endpoint
print("2. Testing GET /api/deals (CRITICAL)")
status, headers, body = test_endpoint("GET", "/api/deals")
print(f"   Status: {status}")

try:
    data = json.loads(body)
    print(f"   Response type: {type(data).__name__}")
    if isinstance(data, dict) and "detail" in data:
        print(f"   Error: {data.get('detail', 'Unknown error')}")
        if "lead_id" in str(data):
            print("   ⚠️  lead_id error still present")
        print("   ❌ FAIL")
    elif isinstance(data, list):
        print(f"   Data count: {len(data)} deals")
        if len(data) > 0:
            print(f"   First deal keys: {list(data[0].keys())[:5]}")
            if 'lead_id' in data[0]:
                print("   ✅ lead_id field present in response")
        print("   ✅ PASS")
    else:
        print(f"   Unexpected response: {str(data)[:100]}")
        print("   ❌ FAIL")
except json.JSONDecodeError:
    print(f"   ❌ Invalid JSON: {body[:100]}")

print()
print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
print("Expected: /health=200, /api/deals=200 with lead_id field")
