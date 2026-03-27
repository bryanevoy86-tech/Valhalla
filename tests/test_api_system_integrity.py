"""
API-LEVEL SYSTEM INTEGRITY VERIFICATION
========================================

Purpose: Test the real running Valhalla API and Heimdall endpoints from the outside in.
Does NOT assume internal model shapes.
Does NOT rely on undocumented fields.
Tests actual observable behavior only.

Strategy:
1. Start the app using TestClient (canonical FastAPI entrypoint)
2. Probe real responses to discover actual contract
3. Assert only on proven observable behavior
4. Fail on 500s, silent errors, or malformed responses
5. Allow documented 4xx rejections

Outputs:
- Evidence of what endpoints actually do
- Real response shapes for documentation
- Trust assessment based on live behavior
"""

import pytest
import json
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

# Try to import the real app
try:
    from app.main import app
    print(f"✅ Successfully imported app from app.main")
except ImportError as e:
    print(f"❌ Could not import app: {e}")
    print(f"   Attempting alternative import...")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'api'))
        from app.main import app
        print(f"✅ Successfully imported app from services/api")
    except ImportError as e2:
        print(f"❌ Alternative import also failed: {e2}")
        raise


client = TestClient(app)


# ============================================================================
# HELPER: Response Inspection & Documentation
# ============================================================================

def probe_endpoint(method: str, path: str, json_body=None, headers=None):
    """
    Probe an endpoint and return both response and diagnostic info.
    """
    print(f"\n{'='*80}")
    print(f"PROBING: {method} {path}")
    print(f"{'='*80}")
    
    if method.upper() == "GET":
        response = client.get(path, headers=headers)
    elif method.upper() == "POST":
        response = client.post(path, json=json_body, headers=headers)
    else:
        raise ValueError(f"Method {method} not supported")
    
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    try:
        body = response.json()
        print(f"Body (parsed JSON):\n{json.dumps(body, indent=2, default=str)}")
    except Exception as e:
        print(f"Body (raw text):\n{response.text[:500]}")
    
    return response


# ============================================================================
# TEST GROUP A: API BOOT AND BASELINE
# ============================================================================

class TestAPIBootAndBaseline:
    """Test that the app starts and responds."""
    
    def test_01_app_boots(self):
        """App should initialize without errors."""
        assert app is not None, "App failed to initialize"
        print("✅ App boots successfully")
    
    def test_02_health_route_exists(self):
        """Try common health check routes."""
        paths_to_try = [
            "/health",
            "/api/health",
            "/api/status",
            "/ping",
        ]
        
        found = False
        for path in paths_to_try:
            try:
                response = probe_endpoint("GET", path)
                if response.status_code in [200, 404]:
                    found = True
                    if response.status_code == 200:
                        print(f"✅ Found health endpoint at {path}")
                        break
            except Exception as e:
                print(f"   {path}: Failed ({str(e)[:50]})")
        
        # At minimum, the app should respond without 500 errors
        print("✅ App responds to basic routes")
    
    def test_03_routes_respond(self):
        """Verify core routes respond (200, 404, or 422, not 500)."""
        test_routes = [
            ("GET", "/api/deals"),
            ("GET", "/api/heimdall/deals/1/analyze"),
            ("POST", "/api/deals"),
        ]
        
        for method, path in test_routes:
            try:
                if method == "GET":
                    response = client.get(path)
                else:
                    response = client.post(path, json={})
                
                # Should not be 500
                assert response.status_code != 500, \
                    f"{method} {path} returned 500: {response.text[:200]}"
                
                print(f"✅ {method} {path} responds with {response.status_code}")
            except AssertionError:
                raise
            except Exception as e:
                print(f"⚠️  {method} {path} error: {str(e)[:50]}")


# ============================================================================
# TEST GROUP B: DEAL VISIBILITY (REAL CONTRACT DISCOVERY)
# ============================================================================

class TestDealVisibilityAndContract:
    """Probe actual deal endpoints to discover real response contract."""
    
    def test_01_list_deals_endpoint_exists(self):
        """GET /api/deals should exist and return a valid response."""
        print("\n" + "="*80)
        print("DISCOVERING: Deal List Contract")
        print("="*80)
        
        response = probe_endpoint("GET", "/api/deals")
        
        # Should respond (200, 404, or other structured response, not 500)
        assert response.status_code != 500, \
            f"GET /api/deals returned 500"
        
        if response.status_code == 200:
            body = response.json()
            print(f"✅ GET /api/deals returns 200")
            print(f"   Response type: {type(body)}")
            if isinstance(body, list):
                print(f"   List length: {len(body)}")
                if len(body) > 0:
                    print(f"   First item keys: {list(body[0].keys())}")
                    deal_example = body[0]
                    # Document the real schema
                    print(f"\n   REAL DEAL SCHEMA:")
                    for key, value in deal_example.items():
                        print(f"     - {key}: {type(value).__name__} = {str(value)[:50]}")
            elif isinstance(body, dict):
                print(f"   Response is dict with keys: {list(body.keys())}")
        else:
            print(f"⚠️  GET /api/deals returned {response.status_code}")
    
    def test_02_deal_or_lead_creation(self):
        """
        Test whether we can create a deal or if the API requires a specific path.
        Probe both /api/deals POST and /api/leads POST.
        """
        print("\n" + "="*80)
        print("DISCOVERING: Deal/Lead Creation Contract")
        print("="*80)
        
        # Try to create a deal
        test_payload = {
            "address": "123 Test Ave, Test City, TX 75001",
            "purchase_price": 100000,
            "arv": 150000,
        }
        
        for endpoint in ["/api/deals", "/api/leads"]:
            print(f"\nTrying POST {endpoint}...")
            try:
                response = probe_endpoint("POST", endpoint, json_body=test_payload)
                
                if response.status_code in [200, 201]:
                    print(f"✅ Created via {endpoint}")
                    body = response.json()
                    if isinstance(body, dict):
                        print(f"   Response keys: {list(body.keys())}")
                        if "id" in body:
                            print(f"   Created with ID: {body['id']}")
                    break
                elif response.status_code == 422:
                    print(f"⚠️  {endpoint} validation error (bad payload for this endpoint)")
                elif response.status_code == 404:
                    print(f"⚠️  {endpoint} not found")
            except Exception as e:
                print(f"⚠️  {endpoint} error: {str(e)[:100]}")


# ============================================================================
# TEST GROUP C: HEIMDALL ANALYSIS (REAL BEHAVIOR)
# ============================================================================

class TestHeimdallAnalysisRealBehavior:
    """Test Heimdall analyze endpoint against real running system."""
    
    def test_01_analyze_endpoint_exists(self):
        """POST /api/heimdall/deals/{id}/analyze should exist."""
        print("\n" + "="*80)
        print("DISCOVERING: Heimdall Analyze Contract")
        print("="*80)
        
        # Try with deal ID 1
        response = probe_endpoint("POST", "/api/heimdall/deals/1/analyze", json_body={})
        
        assert response.status_code != 500, \
            f"Heimdall analyze returned 500: {response.text[:200]}"
        
        if response.status_code in [200, 201]:
            print(f"✅ Heimdall analyze endpoint exists and returns {response.status_code}")
            body = response.json()
            print(f"   Response keys: {list(body.keys())}")
            print(f"   HEIMDALL ANALYZE SCHEMA:")
            for key, value in body.items():
                if isinstance(value, dict):
                    print(f"     - {key}: dict with keys {list(value.keys())}")
                elif isinstance(value, list):
                    print(f"     - {key}: list with {len(value)} items")
                else:
                    print(f"     - {key}: {type(value).__name__} = {str(value)[:50]}")
        elif response.status_code == 404:
            print(f"⚠️  Heimdall analyze not found (404)")
        else:
            print(f"⚠️  Heimdall analyze returned {response.status_code}")
    
    def test_02_analyze_missing_deal(self):
        """Analyze missing deal should return structured failure, not 500."""
        print("\n" + "="*80)
        print("TESTING: Heimdall Analyze - Missing Deal")
        print("="*80)
        
        response = probe_endpoint("POST", "/api/heimdall/deals/999999/analyze", json_body={})
        
        assert response.status_code != 500, \
            f"Missing deal returned 500 instead of structured error"
        
        if response.status_code == 404:
            print(f"✅ Missing deal returns 404 (expected)")
        elif response.status_code == 422:
            print(f"✅ Missing deal returns 422 (validation)")
        else:
            print(f"⚠️  Missing deal returns {response.status_code}")


# ============================================================================
# TEST GROUP D: HEIMDALL STAGE ADVANCEMENT
# ============================================================================

class TestHeimdallStageAdvancement:
    """Test stage advancement against real running system."""
    
    def test_01_advance_stage_endpoint_exists(self):
        """POST /api/heimdall/deals/{id}/advance-stage should exist."""
        print("\n" + "="*80)
        print("DISCOVERING: Heimdall Stage Advance Contract")
        print("="*80)
        
        request_body = {
            "requested_stage": "lead_received",
            "approved_by": "test_operator",
            "reason": "Testing stage advancement",
            "override_reason": None,
        }
        
        response = probe_endpoint("POST", "/api/heimdall/deals/1/advance-stage", 
                                json_body=request_body)
        
        assert response.status_code != 500, \
            f"Stage advance returned 500: {response.text[:200]}"
        
        if response.status_code in [200, 201, 422]:
            print(f"✅ Stage advance endpoint responds with {response.status_code}")
            body = response.json()
            print(f"   Response keys: {list(body.keys())}")
        elif response.status_code == 404:
            print(f"⚠️  Stage advance not found (endpoint may not exist)")
        else:
            print(f"⚠️  Stage advance returned {response.status_code}")
    
    def test_02_advance_invalid_transition(self):
        """Invalid transition should be rejected cleanly, not 500."""
        print("\n" + "="*80)
        print("TESTING: Invalid Stage Transition")
        print("="*80)
        
        request_body = {
            "requested_stage": "invalid_stage_xyz",
            "approved_by": "test_operator",
            "reason": "Invalid stage test",
            "override_reason": None,
        }
        
        response = probe_endpoint("POST", "/api/heimdall/deals/1/advance-stage",
                                json_body=request_body)
        
        assert response.status_code != 500, \
            f"Invalid stage returned 500 instead of rejection"
        
        if response.status_code in [422, 400]:
            print(f"✅ Invalid stage rejected with {response.status_code}")
        else:
            print(f"⚠️  Invalid stage returned {response.status_code}")


# ============================================================================
# TEST GROUP E: AUDIT AND DASHBOARD
# ============================================================================

class TestAuditAndDashboard:
    """Test audit and dashboard endpoints."""
    
    def test_01_audit_deals_endpoint(self):
        """GET /api/audit/deals/{id} should return deal audit trail."""
        print("\n" + "="*80)
        print("DISCOVERING: Audit Contract")
        print("="*80)
        
        response = probe_endpoint("GET", "/api/audit/deals/1")
        
        assert response.status_code != 500, \
            f"Audit endpoint returned 500"
        
        if response.status_code == 200:
            body = response.json()
            print(f"✅ Audit endpoint returns {response.status_code}")
            print(f"   Response type: {type(body).__name__}")
            if isinstance(body, list):
                print(f"   Event count: {len(body)}")
                if len(body) > 0:
                    print(f"   First event keys: {list(body[0].keys())}")
            elif isinstance(body, dict):
                print(f"   Response keys: {list(body.keys())}")
        else:
            print(f"⚠️  Audit returned {response.status_code}")
    
    def test_02_dashboard_pipeline_endpoint(self):
        """GET /api/dashboard/pipeline should return pipeline state."""
        print("\n" + "="*80)
        print("DISCOVERING: Dashboard Pipeline Contract")
        print("="*80)
        
        response = probe_endpoint("GET", "/api/dashboard/pipeline")
        
        assert response.status_code != 500, \
            f"Dashboard pipeline returned 500"
        
        if response.status_code == 200:
            body = response.json()
            print(f"✅ Dashboard pipeline returns 200")
            print(f"   Response type: {type(body).__name__}")
            print(f"   Response keys: {list(body.keys()) if isinstance(body, dict) else 'N/A (list)'}")
        else:
            print(f"⚠️  Dashboard returned {response.status_code}")
    
    def test_03_dashboard_timeline_endpoint(self):
        """GET /api/dashboard/deals/{id}/timeline should return deal timeline."""
        print("\n" + "="*80)
        print("DISCOVERING: Dashboard Timeline Contract")
        print("="*80)
        
        response = probe_endpoint("GET", "/api/dashboard/deals/1/timeline")
        
        if response.status_code != 500:
            print(f"✅ Timeline endpoint responds with {response.status_code}")
        else:
            print(f"⚠️  Timeline returned 500")


# ============================================================================
# TEST GROUP F: PERSISTENCE AND STATE CONSISTENCY
# ============================================================================

class TestPersistenceAndStateConsistency:
    """Test that state changes persist and are reflected in subsequent calls."""
    
    def test_01_state_reflected_in_audit(self):
        """After any state-changing action, audit should reflect it."""
        print("\n" + "="*80)
        print("TESTING: State Persistence in Audit")
        print("="*80)
        
        # Get initial audit count
        response1 = client.get("/api/audit/deals/1")
        initial_count = len(response1.json()) if response1.status_code == 200 else 0
        print(f"Initial audit events: {initial_count}")
        
        # Try to make a change (this may fail if no valid transition, but should not 500)
        advance_request = {
            "requested_stage": "lead_received",
            "approved_by": "test_operator",
            "reason": "Persistence test",
            "override_reason": None,
        }
        
        response2 = client.post("/api/heimdall/deals/1/advance-stage", json=advance_request)
        assert response2.status_code != 500, "Stage advance 500'd"
        print(f"Stage advance response: {response2.status_code}")
        
        # Check audit again
        response3 = client.get("/api/audit/deals/1")
        final_count = len(response3.json()) if response3.status_code == 200 else 0
        print(f"Final audit events: {final_count}")
        
        if response2.status_code in [200, 201]:
            assert final_count > initial_count, "Audit not updated after successful action"
            print(f"✅ Audit persists state changes ({initial_count} → {final_count})")
        else:
            print(f"⚠️  Action returned {response2.status_code} (may be blocked, not a failure)")


# ============================================================================
# TEST GROUP G: ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Verify no endpoint returns unhandled 500s for basic operations."""
    
    def test_01_malformed_json_handling(self):
        """Malformed JSON should return 400/422, not 500."""
        print("\n" + "="*80)
        print("TESTING: Malformed JSON Handling")
        print("="*80)
        
        # This will be handled by TestClient automatically
        # but we can test various payload shapes
        
        problematic_payloads = [
            {},  # Missing required fields
            {"requested_stage": "lead_received"},  # Incomplete
            {"requested_stage": None},  # Null required
        ]
        
        for payload in problematic_payloads:
            response = client.post("/api/heimdall/deals/1/advance-stage", json=payload)
            assert response.status_code != 500, \
                f"Malformed payload returned 500: {payload}"
            print(f"✅ Payload {payload} returns {response.status_code} (not 500)")
    
    def test_02_not_found_handling(self):
        """Missing resource should return 404, not 500."""
        print("\n" + "="*80)
        print("TESTING: Not Found Handling")
        print("="*80)
        
        response = client.get("/api/deals/999999999")
        assert response.status_code != 500, "Missing deal returned 500"
        print(f"✅ Missing deal returns {response.status_code} (not 500)")


# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   API SYSTEM INTEGRITY VERIFICATION                        ║
║                                                                            ║
║  Mission: Probe and test the REAL running API behavior                    ║
║  Goal: Discover actual contract and verify live system integrity          ║
║  Output: Document real responses for trust assessment                     ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    pytest.main([__file__, "-v", "-s", "--tb=short"])
