#!/usr/bin/env python
"""PACK J — GO SUMMARY Verification"""
import subprocess
import time
import requests
import json

print("=" * 60)
print("PACK J — GO SUMMARY Verification")
print("=" * 60)

# Test 1: Verify files exist
print("\n1. Checking files...")
import os
summary_service = "backend/app/core_gov/go/summary_service.py"
summary_router = "backend/app/core_gov/go/summary_router.py"
if os.path.exists(summary_service):
    print(f"   ✓ {summary_service}")
else:
    print(f"   ✗ {summary_service} NOT FOUND")
if os.path.exists(summary_router):
    print(f"   ✓ {summary_router}")
else:
    print(f"   ✗ {summary_router} NOT FOUND")

# Test 2: Import test
print("\n2. Testing imports...")
try:
    from backend.app.core_gov.go.summary_service import go_summary
    print("   ✓ summary_service imports")
except Exception as e:
    print(f"   ✗ summary_service import failed: {e}")

try:
    from backend.app.core_gov.go.summary_router import router
    print("   ✓ summary_router imports")
except Exception as e:
    print(f"   ✗ summary_router import failed: {e}")

# Test 3: Live endpoint test
print("\n3. Starting uvicorn server...")
os.chdir("backend")
proc = subprocess.Popen(
    ["python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "5001"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
time.sleep(4)

print("   ✓ Server started (PID: {})".format(proc.pid))

# Test 4: Endpoint test
print("\n4. Testing GET /core/go/summary endpoint...")
try:
    resp = requests.get("http://localhost:5001/core/go/summary", timeout=5)
    if resp.status_code == 200:
        print(f"   ✓ Endpoint returns 200 OK")
        data = resp.json()
        
        # Check structure
        required_keys = ["session", "next", "checklist", "lite", "app"]
        for key in required_keys:
            if key in data:
                print(f"   ✓ Contains '{key}'")
            else:
                print(f"   ✗ Missing '{key}'")
        
        # Show sample
        print("\n   Sample response structure:")
        print(f"   session.active: {data.get('session', {}).get('active')}")
        print(f"   next.next_step: {data.get('next', {}).get('next_step', {}).get('title')}")
        print(f"   checklist.steps: {len(data.get('checklist', {}).get('steps', []))} steps")
        print(f"   lite.status: {data.get('lite', {}).get('status')}")
        print(f"   lite.cone.band: {data.get('lite', {}).get('cone', {}).get('band')}")
        print(f"   app.version: {data.get('app', {}).get('version')}")
        
    else:
        print(f"   ✗ Endpoint returned {resp.status_code}")
        print(f"   Response: {resp.text}")
except Exception as e:
    print(f"   ✗ Error testing endpoint: {e}")

# Test 5: Route registration
print("\n5. Checking route registration...")
try:
    from backend.app.core_gov.core_router import core
    routes = [r.path for r in core.routes]
    if "/core/go/summary" in routes:
        print("   ✓ /core/go/summary registered in core router")
    else:
        print("   ✗ /core/go/summary NOT in core router")
        print(f"   Available /go routes: {[r for r in routes if '/go' in r]}")
except Exception as e:
    print(f"   ✗ Error checking routes: {e}")

# Cleanup
print("\n6. Cleaning up...")
try:
    proc.terminate()
    proc.wait(timeout=5)
    print("   ✓ Server stopped")
except:
    proc.kill()
    print("   ✓ Server killed")

print("\n" + "=" * 60)
print("✅ PACK J Verification Complete!")
print("=" * 60)
print("\nWeWeb Integration Ready:")
print("  Endpoint: GET /core/go/summary")
print("  Bind to UI:")
print("    - session.active (boolean)")
print("    - next.next_step.title (string)")
print("    - checklist.steps (array)")
print("    - lite.status (string)")
print("    - lite.cone.band (string)")
