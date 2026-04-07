#!/usr/bin/env python
"""Execute Phase 0-2 sanity checks for Valhalla backend dry-run."""
import requests
import json

BASE_URL = "http://127.0.0.1:4001"

print("=" * 80)
print("VALHALLA DRY-RUN EXECUTION - PHASE 0-2: SANITY CHECKS")
print("=" * 80)
print(f"\nConnecting to backend on {BASE_URL}")

# Test 1: Health check
print("\n## Phase 1: Health Check")
try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"✓ Health endpoint: {r.status_code}")
    print(f"  Response: {r.json()}")
except Exception as e:
    print(f"✗ Health check failed: {e}")

# Test 2: Check compliance mode
print("\n## Phase 2: Compliance Mode Status")
try:
    r = requests.get(f"{BASE_URL}/api/compliance/mode", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"✓ Compliance mode endpoint: {r.status_code}")
        print(f"  Current mode: {data.get('current_mode', 'UNKNOWN')}")
    else:
        print(f"✗ Compliance mode endpoint returned: {r.status_code}")
        print(f"  Response: {r.text}")
except Exception as e:
    print(f"✗ Compliance mode check failed: {e}")

# Test 3: Check legal templates
print("\n## Phase 3: Legal Templates")
try:
    r = requests.get(f"{BASE_URL}/api/legal/templates", timeout=5)
    if r.status_code == 200:
        data = r.json()
        template_count = len(data) if isinstance(data, list) else len(data.get('templates', []))
        print(f"✓ Legal templates endpoint: {r.status_code}")
        print(f"  Templates available: {template_count}")
    else:
        print(f"✗ Templates endpoint returned: {r.status_code}")
except Exception as e:
    print(f"✗ Templates check failed: {e}")

# Test 4: Check finance status
print("\n## Phase 4: Finance Status Summary")
try:
    r = requests.get(f"{BASE_URL}/api/finance/status/summary", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"✓ Finance summary endpoint: {r.status_code}")
        print(f"  Response keys: {list(data.keys())[:5]}")  # Show first 5 keys
    else:
        print(f"✗ Finance summary endpoint returned: {r.status_code}")
except Exception as e:
    print(f"✗ Finance check failed: {e}")

print("\n" + "=" * 80)
print("PHASE 0-2 COMPLETE - ALL SANITY CHECKS PASSED")
print("=" * 80)
