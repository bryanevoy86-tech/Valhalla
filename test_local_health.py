#!/usr/bin/env python
"""
Local health check for Valhalla backend.

Tests:
1. GET /health endpoint
2. POST /ops/token with environment credentials

Run this AFTER backend is started:
    python test_local_health.py
"""

import os
import sys
import json
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)


BASE_URL = "http://127.0.0.1:4000"

# Tests
def test_health():
    """Test GET /health endpoint"""
    print("\n[1/2] Testing GET /health...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=3)
        resp.raise_for_status()
        data = resp.json()
        print(f"✓ Health check passed")
        print(f"  Status code: {resp.status_code}")
        print(f"  Response: {json.dumps(data, indent=2)}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_login():
    """Test POST /ops/token with bootstrap credentials"""
    print("\n[2/2] Testing POST /ops/token...")
    
    # Read credentials from environment
    username = os.getenv("VALHALLA_OWNER_USERNAME", "").strip()
    password = os.getenv("VALHALLA_OWNER_PASSWORD", "").strip()
    
    if not username or not password:
        print("⚠ Skipping login test - VALHALLA_OWNER_USERNAME or VALHALLA_OWNER_PASSWORD not set")
        print("  To test login, set env vars:")
        print("    $env:VALHALLA_OWNER_USERNAME='admin'")
        print("    $env:VALHALLA_OWNER_PASSWORD='admin-change-me'")
        return None
    
    try:
        resp = requests.post(
            f"{BASE_URL}/ops/token",
            data={"username": username, "password": password},
            timeout=3
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ Login successful")
            print(f"  Status code: {resp.status_code}")
            print(f"  Token type: {data.get('token_type')}")
            print(f"  Expires in: {data.get('expires_in')} seconds")
            print(f"  Access token (first 50 chars): {data.get('access_token', '')[:50]}...")
            return True
        else:
            print(f"✗ Login failed")
            print(f"  Status code: {resp.status_code}")
            print(f"  Response: {resp.text}")
            return False
    except Exception as e:
        print(f"✗ Login test error: {e}")
        return False


def main():
    print("=" * 70)
    print("VALHALLA LOCAL HEALTH CHECK")
    print("=" * 70)
    print(f"Base URL: {BASE_URL}")
    
    health_ok = test_health()
    login_ok = test_login()
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Health endpoint:   {'✓ PASSED' if health_ok else '✗ FAILED'}")
    print(f"Login endpoint:    {'✓ PASSED' if login_ok else ('⚠ SKIPPED' if login_ok is None else '✗ FAILED')}")
    
    if health_ok:
        print("\n✓ Backend is responding. Ready for WeWeb integration.")
        return 0
    else:
        print("\n✗ Backend is not responding. Check startup logs.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
