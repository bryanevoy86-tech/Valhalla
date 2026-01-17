"""Quick live endpoint test for PACK C."""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

print("\n" + "=" * 70)
print("PACK C - LIVE ENDPOINT TEST")
print("=" * 70 + "\n")

# Start test app
proc = subprocess.Popen(
    [sys.executable, "test_gov_app.py"],
    cwd=Path(__file__).parent,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

try:
    time.sleep(3)
    
    endpoints = [
        ("GET", "/core/healthz"),
        ("GET", "/core/config/thresholds"),
        ("GET", "/core/notify"),
        ("GET", "/core/status/ryg"),
        ("GET", "/core/dashboard"),
        ("GET", "/core/capital/status"),
        ("GET", "/core/alerts"),
        ("GET", "/core/visibility/summary"),
    ]
    
    results = []
    for method, path in endpoints:
        url = f"http://localhost:5000{path}"
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                data = json.loads(resp.read())
                keys = list(data.keys())[:2] if isinstance(data, dict) else type(data).__name__
                results.append((path, resp.status, "OK", str(keys)))
                print(f"[OK] {method:4s} {path:40s} -> {resp.status}")
        except Exception as e:
            results.append((path, "ERR", "FAIL", str(e)[:50]))
            print(f"[FAIL] {method:4s} {path:40s} -> {str(e)[:40]}")
    
    passed = sum(1 for _, status, _, _ in results if status == "OK" or status == 200)
    print(f"\nPassed: {passed}/{len(endpoints)}")
    
finally:
    proc.terminate()
    proc.wait(timeout=2)

print("\n" + "=" * 70)
print("LIVE ENDPOINT TEST COMPLETE")
print("=" * 70 + "\n")
