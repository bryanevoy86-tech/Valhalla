"""Quick test of PACK B endpoints."""
import time
import json
import subprocess
import sys
import os
from pathlib import Path

# Add to path properly
sys.path.insert(0, str(Path(__file__).parent / "backend" / "app"))

# Test imports first
print("=" * 60)
print("PACK B IMPORT TEST")
print("=" * 60)

try:
    from core_gov.analytics.log_tail import tail_lines
    from core_gov.analytics.decisions import decision_stats
    from core_gov.capital.store import load_usage, save_usage
    from core_gov.health.status import ryg_status
    print("[OK] All analytics imports successful")
    print("[OK] All capital imports successful")
    print("[OK] All health imports successful")
except ImportError as e:
    print(f"[FAIL] Import failed: {e}")
    sys.exit(1)

# Test functions
print("\n" + "=" * 60)
print("PACK B FUNCTION TEST")
print("=" * 60)

try:
    # Test analytics
    stats = decision_stats(last_n=50)
    print(f"[OK] decision_stats(): {json.dumps(stats, indent=2)[:200]}...")
    
    # Test capital
    usage = load_usage()
    print(f"[OK] load_usage(): {usage}")
    
    save_usage({"fx_arbitrage": 50000.0})
    updated = load_usage()
    print(f"[OK] save_usage() + load_usage(): {updated}")
    
    # Test status
    status = ryg_status()
    print(f"[OK] ryg_status(): level={status.get('status')}, reasons={len(status.get('reasons', []))} items")
    
except Exception as e:
    print(f"[FAIL] Function test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("PACK B ENDPOINT TEST")
print("=" * 60)

# Start app
proc = subprocess.Popen(
    [sys.executable, "test_gov_app.py"],
    cwd=Path(__file__).parent,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

try:
    time.sleep(3)
    
    import urllib.request
    import urllib.error
    
    endpoints = [
        ("/core/healthz", None),
        ("/core/status/ryg", None),
        ("/core/capital/status", None),
        ("/core/reality/weekly_audit", None),
    ]
    
    for endpoint, method in endpoints:
        url = f"http://localhost:5000{endpoint}"
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                data = json.loads(resp.read())
                print(f"[OK] {endpoint} -> {resp.status} (keys: {list(data.keys())[:3]}...)")
        except Exception as e:
            print(f"[FAIL] {endpoint} -> {e}")
    
    # Test POST to capital
    print("\nTesting POST /core/capital/set:")
    import urllib.request
    import json
    
    payload = json.dumps({"engine": "wholesaling", "used_usd": 25000}).encode()
    req = urllib.request.Request(
        "http://localhost:5000/core/capital/set",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read())
            print(f"[OK] POST /core/capital/set -> {resp.status}: {data}")
    except Exception as e:
        print(f"[FAIL] POST /core/capital/set -> {e}")
    
finally:
    proc.terminate()
    proc.wait(timeout=2)

print("\n" + "=" * 60)
print("PACK B TESTS COMPLETE")
print("=" * 60)
