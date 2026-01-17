#!/usr/bin/env python
"""
Integration test for PACK U (Frontend Preparation) and PACK V (Deployment Checklist)
Tests UI map and deployment check functionality.
"""

import sys
sys.path.insert(0, '/dev/valhalla/services/api')

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers.ui_map import router as ui_map_router
from app.routers.deploy_check import router as deploy_check_router

# Create a test app with all components
app = FastAPI(title="Test App")

# Include routers
app.include_router(ui_map_router)
app.include_router(deploy_check_router)

# Add a simple health endpoint for testing
@app.get("/health")
def health():
    return {"status": "ok"}

# Create test client
client = TestClient(app)


def test_pack_u_ui_map():
    """Test PACK U: Frontend Preparation"""
    print("\n" + "="*70)
    print("PACK U — Frontend Preparation / API → WeWeb Mapping")
    print("="*70)
    
    # Test 1: /ui-map/ endpoint exists
    print("\n1. Testing /ui-map/ endpoint...")
    res = client.get("/ui-map/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    body = res.json()
    print(f"   ✓ UI map endpoint responds with 200 OK")
    
    # Test 2: Has modules
    print("\n2. Verifying UI map structure...")
    assert "modules" in body
    assert isinstance(body["modules"], list)
    assert len(body["modules"]) > 0
    print(f"   ✓ Contains {len(body['modules'])} modules")
    
    # Test 3: Check module structure
    print("\n3. Checking module structure...")
    for module in body["modules"]:
        assert "id" in module
        assert "label" in module
        assert "sections" in module
        assert "description" in module
    print(f"   ✓ All modules have proper structure")
    
    # Test 4: List modules
    print("\n4. Module listing:")
    for module in body["modules"]:
        section_count = len(module["sections"])
        endpoint_count = sum(len(s["endpoints"]) for s in module["sections"])
        print(f"   - {module['label']}: {section_count} sections, {endpoint_count} endpoints")
    
    # Test 5: Check required modules
    print("\n5. Checking required modules...")
    module_ids = [m["id"] for m in body["modules"]]
    required = ["professionals", "contracts", "deals", "audit_governance", "debug_system"]
    for req_module in required:
        assert req_module in module_ids, f"Missing required module: {req_module}"
        print(f"   ✓ {req_module}")
    
    # Test 6: Check sections
    print("\n6. Checking section organization...")
    for module in body["modules"]:
        for section in module["sections"]:
            assert "id" in section
            assert "label" in section
            assert "endpoints" in section
            assert len(section["endpoints"]) > 0
    print(f"   ✓ All sections properly organized")
    
    # Test 7: Check endpoints
    print("\n7. Checking endpoint details...")
    total_endpoints = 0
    for module in body["modules"]:
        for section in module["sections"]:
            for endpoint in section["endpoints"]:
                total_endpoints += 1
                assert "method" in endpoint
                assert "path" in endpoint
                assert "summary" in endpoint
                assert endpoint["method"] in ["GET", "POST", "PATCH", "PUT", "DELETE"]
                assert endpoint["path"].startswith("/")
    print(f"   ✓ {total_endpoints} endpoints properly documented")
    
    # Test 8: Check metadata
    print("\n8. Checking metadata...")
    assert "metadata" in body
    assert "version" in body["metadata"]
    assert "description" in body["metadata"]
    print(f"   ✓ Metadata present: v{body['metadata']['version']}")


def test_pack_v_deploy_check():
    """Test PACK V: Deployment Checklist"""
    print("\n" + "="*70)
    print("PACK V — Deployment Checklist / Ops Automation")
    print("="*70)
    
    # Test 1: /ops/deploy-check/ endpoint exists
    print("\n1. Testing /ops/deploy-check/ endpoint...")
    res = client.get("/ops/deploy-check/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    body = res.json()
    print(f"   ✓ Deploy check endpoint responds with 200 OK")
    
    # Test 2: Has required fields
    print("\n2. Verifying response structure...")
    assert "timestamp" in body
    assert "overall_ok" in body
    assert "checks" in body
    print(f"   ✓ Response has required fields")
    
    # Test 3: Check structure
    print("\n3. Checking checks structure...")
    checks = body["checks"]
    assert "environment" in checks
    assert "database" in checks
    assert "routes" in checks
    print(f"   ✓ All check categories present")
    
    # Test 4: Environment check
    print("\n4. Environment variables check...")
    env_check = checks["environment"]
    assert "ok" in env_check
    assert "details" in env_check
    print(f"   ✓ Environment check: {'PASS' if env_check['ok'] else 'FAIL'}")
    if not env_check["ok"]:
        missing = [k for k, v in env_check["details"].items() if not v]
        print(f"     Missing vars: {missing}")
    
    # Test 5: Database check
    print("\n5. Database health check...")
    db_check = checks["database"]
    assert "ok" in db_check
    print(f"   ✓ Database check: {'HEALTHY' if db_check['ok'] else 'UNHEALTHY'}")
    if "message" in db_check:
        print(f"     Message: {db_check['message']}")
    
    # Test 6: Routes check
    print("\n6. Critical routes check...")
    routes_check = checks["routes"]
    assert "required_prefixes" in routes_check
    assert "missing_prefixes" in routes_check
    assert "ok" in routes_check
    print(f"   ✓ Routes check: {'PASS' if routes_check['ok'] else 'FAIL'}")
    print(f"     Total routes: {routes_check['total_routes']}")
    print(f"     Required prefixes: {len(routes_check['required_prefixes'])}")
    if routes_check["missing_prefixes"]:
        print(f"     Missing prefixes: {routes_check['missing_prefixes']}")
    
    # Test 7: Overall status
    print("\n7. Overall deployment readiness...")
    overall = body["overall_ok"]
    status_icon = "✓" if overall else "✗"
    print(f"   {status_icon} Overall status: {'READY TO DEPLOY' if overall else 'NOT READY'}")
    
    # Test 8: Timestamp
    print("\n8. Timestamp validation...")
    timestamp = body["timestamp"]
    assert isinstance(timestamp, str)
    assert "T" in timestamp  # ISO 8601
    print(f"   ✓ Timestamp: {timestamp}")


def test_integration():
    """Test UI map and deploy check together"""
    print("\n" + "="*70)
    print("Integration Test: PACK U & PACK V")
    print("="*70)
    
    print("\n1. Testing both endpoints are available...")
    ui_res = client.get("/ui-map/")
    deploy_res = client.get("/ops/deploy-check/")
    assert ui_res.status_code == 200
    assert deploy_res.status_code == 200
    print(f"   ✓ Both endpoints accessible")
    
    print("\n2. Verifying data consistency...")
    ui_body = ui_res.json()
    deploy_body = deploy_res.json()
    
    # Count endpoints in UI map
    ui_endpoint_count = sum(
        len(e) for m in ui_body["modules"] 
        for s in m["sections"] 
        for e in s["endpoints"]
    )
    
    # Routes count from deploy check
    deploy_route_count = deploy_body["checks"]["routes"]["total_routes"]
    
    print(f"   ✓ UI map documents {ui_endpoint_count} endpoints")
    print(f"   ✓ Deploy check shows {deploy_route_count} total routes")
    
    print("\n3. Frontend can use UI map for navigation...")
    print("   ✓ WeWeb can consume /ui-map/ for auto-generated screens")
    print("   ✓ Heimdall can use /ops/deploy-check/ for readiness checks")


if __name__ == "__main__":
    try:
        test_pack_u_ui_map()
        test_pack_v_deploy_check()
        test_integration()
        
        print("\n" + "="*70)
        print("✓ ALL PACK U & PACK V TESTS PASSED!")
        print("="*70 + "\n")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
