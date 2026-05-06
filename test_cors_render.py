#!/usr/bin/env python
"""Test CORS headers on Render deployment."""
import requests
import time

BASE_URL = "https://valhalla-api-ha6a.onrender.com"

print("=== Testing CORS Headers on Render ===\n")
time.sleep(2)  # Give Render a moment to deploy

# Test 1: GET /health
print("1. GET /health")
try:
    r = requests.get(f"{BASE_URL}/health", timeout=10)
    print(f"   Status: {r.status_code}")
    cors_header = r.headers.get("access-control-allow-origin", "NOT SET")
    print(f"   Access-Control-Allow-Origin: {cors_header}")
    if cors_header and cors_header != "NOT SET":
        print("   ✓ CORS HEADER PRESENT\n")
    else:
        print("   ✗ CORS HEADER MISSING\n")
except Exception as e:
    print(f"   ✗ Error: {e}\n")

# Test 2: GET /deals
print("2. GET /deals")
try:
    r = requests.get(f"{BASE_URL}/deals", timeout=10)
    print(f"   Status: {r.status_code}")
    cors_header = r.headers.get("access-control-allow-origin", "NOT SET")
    print(f"   Access-Control-Allow-Origin: {cors_header}")
    if cors_header and cors_header != "NOT SET":
        print("   ✓ CORS HEADER PRESENT")
        data = r.json()
        if isinstance(data, list):
            print(f"   Total deals: {len(data)}\n")
    else:
        print("   ✗ CORS HEADER MISSING\n")
except Exception as e:
    print(f"   ✗ Error: {e}\n")

# Test 3: OPTIONS /deals (preflight)
print("3. OPTIONS /deals (CORS preflight)")
try:
    r = requests.options(f"{BASE_URL}/deals", timeout=10)
    print(f"   Status: {r.status_code}")
    print(f"   Access-Control-Allow-Origin: {r.headers.get('access-control-allow-origin', 'NOT SET')}")
    print(f"   Access-Control-Allow-Methods: {r.headers.get('access-control-allow-methods', 'NOT SET')}")
    print(f"   Access-Control-Allow-Headers: {r.headers.get('access-control-allow-headers', 'NOT SET')}")
    print("   ✓ PREFLIGHT RESPONSE\n")
except Exception as e:
    print(f"   ✗ Error: {e}\n")

print("=== Summary ===")
print("If all endpoints show 'CORS HEADER PRESENT',")
print("then WeWeb frontend can now successfully call GET /deals and GET /health")
