#!/usr/bin/env python
"""Retest all 10 endpoints after fixes on port 8000"""

import requests
import time

BASE_URL = "http://localhost:8000"

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

print("=" * 80)
print("ENDPOINT RETEST RESULTS")
print("=" * 80)

for idx, (method, endpoint) in enumerate(endpoints, 1):
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, timeout=5)
        
        status = response.status_code
        print(f"\n{idx}. {method:5} {endpoint}")
        print(f"   Status: {status}")
        
        # Truncate long responses
        resp_text = response.text
        if len(resp_text) > 150:
            resp_text = resp_text[:150] + "..."
        print(f"   Response: {resp_text}")
        
        if status == 200:
            print("                             ✅ PASS")
        else:
            print("                             ⚠️ WARN")
            
    except Exception as e:
        print(f"\n{idx}. {method:5} {endpoint}")
        print(f"   Error: {str(e)}")
        print("                             ❌ FAIL")

print("\n" + "=" * 80)
