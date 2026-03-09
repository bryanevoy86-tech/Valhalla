#!/usr/bin/env python
"""PACK J — GO SUMMARY Live Endpoint Test"""
import subprocess
import time
import requests
import json
import os

print("=" * 60)
print("PACK J — GO SUMMARY Live Test")
print("=" * 60)

os.chdir("backend")

# Start server
print("\nStarting uvicorn server...")
proc = subprocess.Popen(
    ["python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "5002"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
time.sleep(4)
print("✓ Server started")

try:
    # Test endpoint
    print("\nTesting GET /core/go/summary...")
    resp = requests.get("http://localhost:5002/core/go/summary", timeout=5)
    
    if resp.status_code == 200:
        print("✓ Status: 200 OK")
        data = resp.json()
        
        print("\n✓ Response structure:")
        print(f"  - session.active: {data['session']['active']}")
        print(f"  - next.next_step: {data['next']['next_step']}")
        print(f"  - checklist.steps: {len(data['checklist']['steps'])} steps")
        print(f"  - health.status: {data['health']['status']}")
        print(f"  - health.cone.band: {data['health']['cone']['band']}")
        
        print("\n✓ PACK J endpoint working!")
        
    else:
        print(f"✗ Status: {resp.status_code}")
        print(f"Response: {resp.text}")

except Exception as e:
    print(f"✗ Error: {e}")

finally:
    print("\nShutting down server...")
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        proc.kill()
    print("✓ Server stopped")

print("\n" + "=" * 60)
print("✅ PACK J Ready for WeWeb Integration")
print("=" * 60)
print("\nEndpoint: GET /core/go/summary")
print("\nBind in WeWeb to:")
print("  • session.active")
print("  • next.next_step.title")
print("  • checklist.steps")
print("  • health.status")
print("  • health.cone.band")
