#!/usr/bin/env python
"""PACK I Session Workflow Test - Direct"""
import subprocess
import time
import requests
import json
import os
import signal

# Start uvicorn in separate process
print("=" * 50)
print("PACK I — Session Workflow Test (Direct)")
print("=" * 50)

os.chdir("c:\\dev\\valhalla\\backend")

# Start server
print("\nStarting uvicorn server...")
proc = subprocess.Popen(
    [
        "C:\\dev\\valhalla\\.venv\\Scripts\\python.exe",
        "-m", "uvicorn",
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", "5000"
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for server to start
time.sleep(5)

base_url = "http://127.0.0.1:5000"
headers = {"Content-Type": "application/json"}

try:
    # Test 1: Get current session
    print("\n1. GET /core/go/session")
    resp = requests.get(f"{base_url}/core/go/session")
    print(f"   Status: {resp.status_code}")
    data = resp.json()
    print(f"   Active: {data.get('active')}")
    print(f"   Status: {data.get('status')}")
    
    # Test 2: Start session
    print("\n2. POST /core/go/start_session")
    resp = requests.post(
        f"{base_url}/core/go/start_session",
        headers=headers,
        json={"notes": "Testing PACK I session workflow"}
    )
    print(f"   Status: {resp.status_code}")
    data = resp.json()
    print(f"   Active: {data.get('active')}")
    print(f"   Started at: {data.get('started_at_utc')}")
    print(f"   Cone Band: {data.get('cone_band')}")
    
    # Test 3: Get session again
    print("\n3. GET /core/go/session (after start)")
    resp = requests.get(f"{base_url}/core/go/session")
    print(f"   Status: {resp.status_code}")
    data = resp.json()
    print(f"   Active: {data.get('active')} (should be True)")
    
    # Test 4: End session
    print("\n4. POST /core/go/end_session")
    resp = requests.post(
        f"{base_url}/core/go/end_session",
        headers=headers,
        json={"notes": "Session completed"}
    )
    print(f"   Status: {resp.status_code}")
    data = resp.json()
    print(f"   Active: {data.get('active')} (should be False)")
    print(f"   Ended at: {data.get('ended_at_utc')}")
    
    # Test 5: Check persistence
    print("\n5. Checking data/go_session.json")
    session_file = "c:\\dev\\valhalla\\data\\go_session.json"
    if os.path.exists(session_file):
        with open(session_file) as f:
            content = json.load(f)
            session = content.get("session", {})
            print(f"   ✓ File exists")
            print(f"   Active: {session.get('active')}")
            print(f"   Notes: {session.get('notes')}")
    else:
        print(f"   ✗ File not found: {session_file}")
    
    # Test 6: Check playbook endpoint
    print("\n6. Testing playbook coexistence (GET /core/go/checklist)")
    resp = requests.get(f"{base_url}/core/go/checklist")
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        step_count = len(data.get('steps', []))
        print(f"   ✓ Playbook still works ({step_count} steps)")
    else:
        print(f"   ✗ Playbook endpoint failed")
    
    print("\n" + "=" * 50)
    print("✅ Session Workflow Test Complete!")
    print("=" * 50)

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Kill server
    print("\nShutting down server...")
    proc.terminate()
    proc.wait(timeout=5)
    print("Done!")
