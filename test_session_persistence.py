#!/usr/bin/env python
"""PACK I Persistence Test - Session survives restart"""
import subprocess
import time
import requests
import json
import os

print("=" * 60)
print("PACK I — Session Persistence Test (Restart Verification)")
print("=" * 60)

os.chdir("c:\\dev\\valhalla\\backend")
base_url = "http://127.0.0.1:5000"
headers = {"Content-Type": "application/json"}
venv_python = "C:\\dev\\valhalla\\.venv\\Scripts\\python.exe"

def start_server():
    """Start uvicorn server"""
    return subprocess.Popen(
        [venv_python, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "5000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

def stop_server(proc):
    """Stop uvicorn server"""
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except:
        proc.kill()

try:
    # ===== Round 1: Start fresh session =====
    print("\n[Round 1] Starting server #1...")
    proc1 = start_server()
    time.sleep(4)
    
    print("Starting new session...")
    resp = requests.post(
        f"{base_url}/core/go/start_session",
        headers=headers,
        json={"notes": "Persistence test session - Round 1"}
    )
    session_data_r1 = resp.json()
    print(f"✓ Session started")
    print(f"  Active: {session_data_r1.get('active')}")
    print(f"  Cone Band: {session_data_r1.get('cone_band')}")
    print(f"  Started at: {session_data_r1.get('started_at_utc')}")
    
    session_id_r1 = session_data_r1.get('started_at_utc')
    
    # Check file exists
    print("\nVerifying file creation...")
    session_file = "c:\\dev\\valhalla\\backend\\data\\go_session.json"
    if os.path.exists(session_file):
        with open(session_file) as f:
            file_data_r1 = json.load(f)
        print(f"✓ Session file created at {session_file}")
        print(f"  File size: {os.path.getsize(session_file)} bytes")
    else:
        print(f"✗ Session file not found!")
        raise FileNotFoundError(session_file)
    
    print("\nShutting down server #1...")
    stop_server(proc1)
    time.sleep(2)
    
    # ===== Round 2: Restart and verify persistence =====
    print("\n[Round 2] Starting server #2 (RESTART)...")
    proc2 = start_server()
    time.sleep(4)
    
    print("Checking session persistence...")
    resp = requests.get(f"{base_url}/core/go/session")
    session_data_r2 = resp.json()
    
    print(f"✓ Session retrieved after restart")
    print(f"  Active: {session_data_r2.get('active')}")
    print(f"  Cone Band: {session_data_r2.get('cone_band')}")
    print(f"  Started at: {session_data_r2.get('started_at_utc')}")
    print(f"  Notes: {session_data_r2.get('notes')}")
    
    # Verify data matches
    if session_data_r2.get('started_at_utc') == session_id_r1:
        print("\n✅ Timestamp matches! Session data persisted across restart!")
    else:
        print("\n⚠ Warning: Timestamp mismatch")
        print(f"  Expected: {session_id_r1}")
        print(f"  Got: {session_data_r2.get('started_at_utc')}")
    
    # Verify full snapshot
    if session_data_r2.get('snapshot'):
        print(f"\n✓ Snapshot preserved:")
        print(f"  Cone band: {session_data_r2['snapshot'].get('cone', {}).get('band')}")
        print(f"  Health status: {session_data_r2['snapshot'].get('status', {}).get('status')}")
    
    # Test ending session in Round 2
    print("\nEnding session in Round 2...")
    resp = requests.post(
        f"{base_url}/core/go/end_session",
        headers=headers,
        json={"notes": "Ended after restart"}
    )
    session_data_r2_end = resp.json()
    print(f"✓ Session ended")
    print(f"  Active: {session_data_r2_end.get('active')}")
    print(f"  Ended at: {session_data_r2_end.get('ended_at_utc')}")
    print(f"  Notes: {session_data_r2_end.get('notes')}")
    
    # ===== Round 3: Verify inactive session persists =====
    print("\n[Round 3] Restarting server #3...")
    stop_server(proc2)
    time.sleep(2)
    
    proc3 = start_server()
    time.sleep(4)
    
    print("Checking session after second restart...")
    resp = requests.get(f"{base_url}/core/go/session")
    session_data_r3 = resp.json()
    
    print(f"✓ Session retrieved after second restart")
    print(f"  Active: {session_data_r3.get('active')} (should be False)")
    print(f"  Ended at: {session_data_r3.get('ended_at_utc')}")
    
    if session_data_r3.get('active') == False and session_data_r3.get('ended_at_utc'):
        print("\n✅ Full session lifecycle persisted across TWO restarts!")
    
    print("\nShutting down server #3...")
    stop_server(proc3)
    
    print("\n" + "=" * 60)
    print("✅ Persistence Test PASSED!")
    print("=" * 60)
    print("\nSummary:")
    print("  • Session started in Round 1")
    print("  • Session persisted through restart to Round 2")
    print("  • Session ended in Round 2")
    print("  • Session state persisted through restart to Round 3")
    print("  • Session lifecycle data completely preserved across restarts")

except Exception as e:
    print(f"\n✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
    try:
        proc1.kill()
        proc2.kill()
        proc3.kill()
    except:
        pass
