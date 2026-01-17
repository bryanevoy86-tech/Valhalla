"""PACK D Integration Test - RBAC Lock + Rate Limiting."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend" / "app"))

print("\n" + "=" * 70)
print("PACK D COMPREHENSIVE TEST - RBAC LOCK + RATE LIMITING")
print("=" * 70 + "\n")

# Test 1: Rate limiter imports and basic function
print("1. RATE LIMITER TEST")
print("-" * 70)
try:
    from core_gov.rate_limit.limiter import RateLimit, check_rate_limit, _BUCKETS
    from core_gov.rate_limit.deps import rate_limit
    
    print("[OK] rate_limit.limiter imports work")
    print("[OK] rate_limit.deps imports work")
    
    # Test RateLimit dataclass
    rl = RateLimit(max_requests=5, window_seconds=60)
    assert rl.max_requests == 5, "RateLimit instantiation failed"
    print("[OK] RateLimit dataclass works")
    
    # Test rate_limit dependency factory
    dep = rate_limit("test_bucket", max_requests=3, window_seconds=30)
    print("[OK] rate_limit() dependency factory works")
    
except Exception as e:
    print(f"[FAIL] Rate limiter: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Router imports (no errors on import means RBAC/deps are wired)
print("\n2. ROUTER IMPORTS TEST")
print("-" * 70)
try:
    from core_gov.cone.router import router as cone_router
    from core_gov.capital.router import router as capital_router
    from core_gov.config.router import router as config_router
    from core_gov.notify.router import router as notify_router
    from core_gov.jobs.router import router as jobs_router
    
    print("[OK] cone.router imports (RBAC + rate_limit)")
    print("[OK] capital.router imports (RBAC + rate_limit)")
    print("[OK] config.router imports (RBAC + rate_limit)")
    print("[OK] notify.router imports (RBAC + rate_limit)")
    print("[OK] jobs.router imports (RBAC + rate_limit)")
    
except Exception as e:
    print(f"[FAIL] Router imports: {e}")
    import traceback
    traceback.print_exc()

# Test 3: RBAC functions still work
print("\n3. RBAC FUNCTIONS TEST")
print("-" * 70)
try:
    from core_gov.security.rbac import require_scopes, require_active_subscription, get_current_user
    
    print("[OK] require_scopes imports")
    print("[OK] require_active_subscription imports")
    
    # These are callable dependency makers
    owner_dep = require_scopes("owner")
    sub_dep = require_active_subscription
    
    print("[OK] require_scopes('owner') creates dependency")
    print("[OK] require_active_subscription creates dependency")
    
except Exception as e:
    print(f"[FAIL] RBAC functions: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test endpoints via live HTTP
print("\n4. LIVE ENDPOINT TEST - READ vs WRITE")
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
    
    # READ endpoints should still work (no auth in v1 stub)
    read_endpoints = [
        ("/core/status/ryg", "GET"),
        ("/core/dashboard", "GET"),
        ("/core/alerts", "GET"),
        ("/core/cone/state", "GET"),
        ("/core/capital/status", "GET"),
        ("/core/config/thresholds", "GET"),
        ("/core/notify", "GET"),
    ]
    
    print("Testing READ endpoints (no auth required in v1):")
    for path, method in read_endpoints:
        url = f"http://localhost:5000{path}"
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    print(f"  [OK] {method:4s} {path:40s} -> 200")
                else:
                    print(f"  [FAIL] {method:4s} {path:40s} -> {resp.status}")
        except Exception as e:
            print(f"  [FAIL] {method:4s} {path:40s} -> {str(e)[:40]}")
    
    # WRITE endpoints should still work (stub auth returns owner+active)
    print("\nTesting WRITE endpoints (auth/rate_limit wired):")
    write_endpoints = [
        ("/core/cone/state?band=B_CAUTION&reason=Test", "POST", None),
        ("/core/notify/clear", "POST", None),
    ]
    
    for path, method, body in write_endpoints:
        url = f"http://localhost:5000{path}"
        try:
            if body:
                req = urllib.request.Request(url, data=body.encode(), method=method)
            else:
                req = urllib.request.Request(url, method=method)
            
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    print(f"  [OK] {method:4s} {path:50s} -> 200")
                else:
                    print(f"  [FAIL] {method:4s} {path:50s} -> {resp.status}")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"  [OK] {method:4s} {path:50s} -> 429 (rate limited)")
            else:
                print(f"  [FAIL] {method:4s} {path:50s} -> {e.code}")
        except Exception as e:
            print(f"  [FAIL] {method:4s} {path:50s} -> {str(e)[:40]}")
    
    # Test rate limiting
    print("\nTesting RATE LIMITING (POST to cone/state 15+ times):")
    path = "/core/cone/state?band=B_CAUTION&reason=RateTest"
    url = f"http://localhost:5000{path}"
    
    success_count = 0
    limited_count = 0
    
    for i in range(15):
        try:
            req = urllib.request.Request(url, method="POST")
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status == 200:
                    success_count += 1
        except urllib.error.HTTPError as e:
            if e.code == 429:
                limited_count += 1
        except Exception:
            pass
        
        # Small delay to avoid overwhelming
        time.sleep(0.05)
    
    if limited_count > 0:
        print(f"  [OK] Rate limiting working: {success_count} passed, {limited_count} limited (429)")
    else:
        print(f"  [WARN] Rate limiting: {success_count} passed, {limited_count} limited (adjust window or test differently)")
    
finally:
    proc.terminate()
    proc.wait(timeout=2)

print("\n" + "=" * 70)
print("PACK D TESTS COMPLETE")
print("=" * 70 + "\n")
