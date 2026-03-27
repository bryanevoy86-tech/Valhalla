#!/usr/bin/env python
"""Retest all 10 endpoints after fixes"""

import requests
import time

BASE_URL = "http://localhost:4000"

# Wait for server to be ready
time.sleep(2)

endpoints = [
    ("GET", "/exports/month/status?year=2026&month=3"),
    ("POST", "/exports/packs/eia?year=2026&month=3"),
    ("POST", "/exports/packs/accountant?year=2026&month=3"),
    ("POST", "/exports/packs/legal?year=2026&month=3"),
    ("POST", "/exports/packs/appointment/eia?year=2026&month=3"),
    ("POST", "/exports/packs/appointment/eia/close?year=2026&month=3&locked_by=test_user"),
    ("POST", "/exports/packs/appointment/eia/ensure-close?year=2026&month=3&locked_by=test_user"),
    ("POST", "/exports/month/open?year=2026&month=3&opened_by=test_user"),
    ("GET", "/exports/packs/files?year=2026&month=3"),
    ("GET", "/exports/packs/download?package_type=appointment&year=2026&month=3"),
]

print("\n" + "="*80)
print("ENDPOINT RETEST RESULTS")
print("="*80 + "\n")

for idx, (method, endpoint) in enumerate(endpoints, 1):
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            r = requests.get(url, timeout=5)
        elif method == "POST":
            r = requests.post(url, timeout=5)
        
        status = r.status_code
        # Truncate response for readability
        body = r.text[:200] if r.text else "(empty)"
        result = "✅ PASS" if status < 400 else "❌ FAIL" if status >= 500 else "⚠️ WARN"
        
        print(f"{idx}. {method:4} {endpoint}")
        print(f"   Status: {status}")
        print(f"   Response: {body}")
        print(f"   {result}\n")
    except Exception as e:
        print(f"{idx}. {method:4} {endpoint}")
        print(f"   ERROR: {str(e)}\n")

print("="*80)
