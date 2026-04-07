#!/usr/bin/env python3
"""
System Readiness Verification Script
Valhalla Launch Core - Backend Finalization Checklist
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("VALHALLA BACKEND READINESS VERIFICATION")
print(f"Timestamp: {datetime.now().isoformat()}")
print("=" * 80)

# Track results
results = {}
checks_passed = 0
checks_total = 0

def test_endpoint(name, path, expected_status=200):
    """Test an endpoint and report results."""
    global checks_passed, checks_total
    checks_total += 1
    
    try:
        url = f"{BASE_URL}{path}"
        response = requests.get(url, timeout=5)
        status = response.status_code
        passed = status == expected_status
        
        if passed:
            checks_passed += 1
            symbol = "✅"
        else:
            symbol = "❌"
        
        results[name] = {"status": status, "passed": passed}
        print(f"{symbol} {name}: {status} (expected {expected_status})")
        
        return passed
    except Exception as e:
        checks_total += 1
        symbol = "❌"
        results[name] = {"status": "ERROR", "passed": False, "error": str(e)}
        print(f"{symbol} {name}: ERROR - {e}")
        return False

# === SYSTEM HEALTH CHECKS ===
print("\n[1] SYSTEM HEALTH CHECKS")
print("-" * 80)
test_endpoint("Health Check", "/health")
test_endpoint("Health Plus", "/healthz")
test_endpoint("Version Endpoint", "/version")

# === CORE API ENDPOINTS ===
print("\n[2] CORE API ENDPOINTS (Launch Routers)")
print("-" * 80)
test_endpoint("Leads Router", "/api/leads")
test_endpoint("Deals Router", "/api/deals")
test_endpoint("Offers Router", "/api/offers")
test_endpoint("Buyers Router", "/api/buyers")
test_endpoint("Contracts Router", "/api/contracts")
test_endpoint("Audit Router", "/api/audit")

# === EIA COMPLIANCE ===
print("\n[3] EIA COMPLIANCE & REPORTING")
print("-" * 80)
test_endpoint("EIA Status", "/api/eia/status")
test_endpoint("EIA Monthly Report", "/api/eia/monthly-report")
test_endpoint("EIA Check", "/api/eia/check")

# === GOVERNANCE & LAUNCH ===
print("\n[4] GOVERNANCE & LAUNCH STATUS")
print("-" * 80)
test_endpoint("Launch Status", "/api/launch/status")
test_endpoint("Go Button Status", "/api/go-button/status")

# === DOCUMENTATION ===
print("\n[5] DOCUMENTATION & DISCOVERY")
print("-" * 80)
test_endpoint("Swagger UI", "/docs")
test_endpoint("OpenAPI Schema", "/openapi.json")
test_endpoint("Route Discovery", "/__routes")

# === SUMMARY ===
print("\n" + "=" * 80)
print("READINESS SUMMARY")
print("=" * 80)
print(f"Checks Passed: {checks_passed}/{checks_total}")
pass_rate = (checks_passed / checks_total) * 100 if checks_total > 0 else 0
print(f"Pass Rate: {pass_rate:.1f}%")

if checks_passed == checks_total:
    print("\n✅ ALL CHECKS PASSED - System is ready for WeWeb integration!")
elif pass_rate >= 80:
    print("\n⚠️  MOST CHECKS PASSED - System is mostly operational")
else:
    print("\n❌ CRITICAL ISSUES - System needs attention")

# === FEATURE FLAGS ===
print("\n[6] FEATURE FLAGS STATUS")
print("-" * 80)
try:
    from app.core_flags.flags import all_flags
    flags = all_flags()
    print("Active Flags:")
    for flag_name, enabled in flags.items():
        status = "✅" if enabled else "❌"
        print(f"  {status} {flag_name}: {enabled}")
except Exception as e:
    print(f"Could not load feature flags: {e}")

print("\n" + "=" * 80)
print("BACKEND FINALIZATION COMPLETE")
print("=" * 80)
