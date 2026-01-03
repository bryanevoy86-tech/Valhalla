"""PACK C Integration Test - Thresholds, Notifications, Guards, Dashboard."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend" / "app"))

print("\n" + "=" * 70)
print("PACK C COMPREHENSIVE TEST")
print("=" * 70 + "\n")

# Test 1: Threshold Config
print("1. THRESHOLD CONFIG TEST")
print("-" * 70)
try:
    from core_gov.config.thresholds import load_thresholds, save_thresholds, Thresholds
    
    t = load_thresholds()
    print(f"[OK] load_thresholds(): {t.model_dump()}")
    
    # Modify and save
    t.max_failed_jobs_red = 2
    save_thresholds(t)
    
    t2 = load_thresholds()
    assert t2.max_failed_jobs_red == 2, "Failed to persist threshold"
    print(f"[OK] save_thresholds() persistence works")
    print(f"[OK] Thresholds model validation works")
except Exception as e:
    print(f"[FAIL] Threshold config: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Notification Queue
print("\n2. NOTIFICATION QUEUE TEST")
print("-" * 70)
try:
    from core_gov.notify.queue import push, list_all, clear_all
    
    clear_all()
    
    n1 = push("red", "Critical Alert", "System is in RED state", {"cone_band": "C"})
    print(f"[OK] push() creates notification: {n1['id'][:8]}...")
    
    n2 = push("yellow", "Warning", "Deny rate is high")
    
    all_notifs = list_all(limit=10)
    assert len(all_notifs) == 2, f"Expected 2 notifications, got {len(all_notifs)}"
    print(f"[OK] list_all() returns {len(all_notifs)} notifications")
    
    cleared = clear_all()
    assert cleared["ok"], "clear_all() failed"
    empty = list_all()
    assert len(empty) == 0, "clear_all() did not clear notifications"
    print(f"[OK] clear_all() empties queue")
    
except Exception as e:
    print(f"[FAIL] Notification queue: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Guard Helpers
print("\n3. GUARD HELPERS TEST")
print("-" * 70)
try:
    from core_gov.guards.guard import require, forbid, GuardViolation
    
    # Test require - pass
    require(True, "Should pass")
    print(f"[OK] require() passes when condition is true")
    
    # Test require - fail
    try:
        require(False, "This should fail", engine="test")
        print(f"[FAIL] require() should raise GuardViolation")
    except GuardViolation as e:
        print(f"[OK] require() raises GuardViolation when condition is false")
    
    # Test forbid - pass
    forbid(False, "Should pass")
    print(f"[OK] forbid() passes when condition is false")
    
    # Test forbid - fail
    try:
        forbid(True, "This should fail", status="bad")
        print(f"[FAIL] forbid() should raise GuardViolation")
    except GuardViolation:
        print(f"[OK] forbid() raises GuardViolation when condition is true")
    
except Exception as e:
    print(f"[FAIL] Guard helpers: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Enhanced R/Y/G Status with Thresholds
print("\n4. ENHANCED R/Y/G STATUS TEST")
print("-" * 70)
try:
    from core_gov.health.status import ryg_status
    
    status = ryg_status()
    required_keys = ["status", "reasons", "cone", "jobs", "decision_stats", "thresholds"]
    for key in required_keys:
        assert key in status, f"Missing key: {key}"
    
    print(f"[OK] ryg_status() returns all required fields")
    print(f"    - status: {status['status']}")
    print(f"    - reasons: {len(status['reasons'])} items")
    print(f"    - cone band: {status['cone']['band']}")
    print(f"    - jobs: total={status['jobs']['total']}, failed={status['jobs']['failed']}")
    print(f"    - thresholds: max_failed_jobs_red={status['thresholds']['max_failed_jobs_red']}")
    
except Exception as e:
    print(f"[FAIL] Enhanced R/Y/G status: {e}")
    import traceback
    traceback.print_exc()

# Test 5: One-Screen Dashboard
print("\n5. ONE-SCREEN DASHBOARD TEST")
print("-" * 70)
try:
    from core_gov.health.dashboard import one_screen_dashboard
    
    dashboard = one_screen_dashboard()
    required_sections = ["status", "alerts", "capital", "summary"]
    for section in required_sections:
        assert section in dashboard, f"Missing section: {section}"
    
    print(f"[OK] one_screen_dashboard() returns all sections")
    print(f"    - status: {dashboard['status']['status']}")
    print(f"    - alerts: {len(dashboard['alerts']['warnings'])} warnings")
    print(f"    - capital: {len(dashboard['capital']['capped_engines'])} capped engines")
    # cone is a Pydantic model, convert to dict
    cone = dashboard['summary']['cone']
    if hasattr(cone, 'model_dump'):
        cone_band = cone.model_dump()['band']
    else:
        cone_band = cone['band']
    print(f"    - summary: {cone_band} cone band")
    
except Exception as e:
    print(f"[FAIL] One-screen dashboard: {e}")
    import traceback
    traceback.print_exc()

# Test 6: HTTP Endpoints
print("\n6. HTTP ENDPOINTS TEST")
print("-" * 70)

import subprocess
import time
import urllib.request
import urllib.error

proc = subprocess.Popen(
    [sys.executable, "test_gov_app.py"],
    cwd=Path(__file__).parent,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

try:
    time.sleep(3)
    
    endpoints = [
        ("/core/config/thresholds", "GET"),
        ("/core/notify", "GET"),
        ("/core/status/ryg", "GET"),
        ("/core/dashboard", "GET"),
    ]
    
    for endpoint, method in endpoints:
        url = f"http://localhost:5000{endpoint}"
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                data = json.loads(resp.read())
                keys = list(data.keys())[:3] if isinstance(data, dict) else "array"
                print(f"[OK] {endpoint} -> 200 (keys: {keys}...)")
        except Exception as e:
            print(f"[FAIL] {endpoint} -> {e}")
    
    # Test POST to config
    print("\nTesting POST /core/config/thresholds:")
    payload = json.dumps({
        "max_failed_jobs_red": 3,
        "max_failed_jobs_yellow": 1,
        "deny_rate_yellow": 0.25,
        "deny_rate_red": 0.35,
        "min_decisions_for_drift": 20,
        "unhandled_exceptions_red": 1
    }).encode()
    req = urllib.request.Request(
        "http://localhost:5000/core/config/thresholds",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read())
            print(f"[OK] POST /core/config/thresholds -> 200: max_failed_jobs_red={data.get('max_failed_jobs_red')}")
    except Exception as e:
        print(f"[FAIL] POST /core/config/thresholds -> {e}")
    
finally:
    proc.terminate()
    proc.wait(timeout=2)

print("\n" + "=" * 70)
print("PACK C TESTS COMPLETE")
print("=" * 70 + "\n")
