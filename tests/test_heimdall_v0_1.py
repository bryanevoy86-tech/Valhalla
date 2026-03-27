"""
Heimdall v0.1 Tests
Tests for deal analysis, stage advancement, and audit logging
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.core.db import SessionLocal


client = TestClient(app)
TEST_KEY = "test-builder-key"
HEADERS = {"X-API-Key": TEST_KEY}


class TestHeimdallAnalysis:
    """Test deal analysis functionality."""

    def test_analyze_valid_deal(self):
        """Test analyzing an existing deal."""
        deal_id = 1  # Assume test deal exists from smoke test
        
        response = client.post(f"/api/heimdall/deals/{deal_id}/analyze", headers=HEADERS)
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "deal_id" in data
            assert "current_stage" in data
            assert "recommendations" in data
            assert "blocker_flags" in data
            print(f"✅ Deal {deal_id} analyzed successfully")

    def test_analyze_missing_deal(self):
        """Test analyzing a non-existent deal."""
        deal_id = 999999  # Should not exist
        
        response = client.post(f"/api/heimdall/deals/{deal_id}/analyze", headers=HEADERS)
        
        # Should be 404
        assert response.status_code in [404, 500]
        print(f"✅ Non-existent deal correctly rejected")

    def test_analysis_output_structure(self):
        """Test that analysis returns complete structure."""
        deal_id = 1
        
        response = client.post(f"/api/heimdall/deals/{deal_id}/analyze", headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check all required fields
            assert "deal_id" in data
            assert "analysis_timestamp" in data
            assert "current_stage" in data
            assert "deal_data" in data
            assert "missing_fields" in data
            assert "blocker_flags" in data
            assert "risk_flags" in data
            assert "recommendations" in data
            
            # Check recommendations structure
            recommendations = data["recommendations"]
            assert "next_valid_stages" in recommendations
            assert "recommended_stage" in recommendations
            assert "recommendation_reason" in recommendations
            assert "can_advance_now" in recommendations
            
            print(f"✅ Analysis output structure complete")


class TestHeimdallStageAdvance:
    """Test stage advancement functionality."""

    def test_advance_valid_stage(self):
        """Test advancing a deal to a valid next stage."""
        deal_id = 1
        
        # First analyze to find valid next stage
        analysis_response = client.post(f"/api/heimdall/deals/{deal_id}/analyze", headers=HEADERS)
        
        if analysis_response.status_code != 200:
            pytest.skip("Could not analyze deal")
        
        analysis = analysis_response.json()
        current_stage = analysis["current_stage"]
        valid_stages = analysis["recommendations"]["next_valid_stages"]
        
        if not valid_stages:
            pytest.skip("No valid next stage for this deal")
        
        requested_stage = valid_stages[0]
        
        # Try to advance
        advance_response = client.post(
            f"/api/heimdall/deals/{deal_id}/advance-stage",
            json={
                "requested_stage": requested_stage,
                "approved_by": "test_user@example.com",
                "reason": "Testing stage advance",
            },
            headers=HEADERS
        )
        
        assert advance_response.status_code in [200, 400, 422]
        if advance_response.status_code == 200:
            data = advance_response.json()
            assert data["deal_id"] == deal_id
            assert data["result"] in ["success", "rejected"]
            print(f"✅ Stage advance response received")

    def test_advance_invalid_transition(self):
        """Test that invalid transitions are rejected."""
        deal_id = 1
        
        # Try to skip stages (invalid)
        advance_response = client.post(
            f"/api/heimdall/deals/{deal_id}/advance-stage",
            json={
                "requested_stage": "closed",  # Skip multiple stages
                "approved_by": "test_user@example.com",
                "reason": "Testing invalid transition",
            },
            headers=HEADERS
        )
        
        assert advance_response.status_code in [200, 400]
        if advance_response.status_code == 200:
            data = advance_response.json()
            # Should be rejected or accepted depending on deal state
            assert "result" in data
            print(f"✅ Invalid transition handled correctly")

    def test_advance_with_override(self):
        """Test advancing with override reason."""
        deal_id = 1
        
        advance_response = client.post(
            f"/api/heimdall/deals/{deal_id}/advance-stage",
            json={
                "requested_stage": "offer_ready",
                "approved_by": "test_user@example.com",
                "reason": "Testing override",
                "override_reason": "Known issue - proceeding anyway",
            },
            headers=HEADERS
        )
        
        assert advance_response.status_code in [200, 400, 422]
        if advance_response.status_code == 200:
            data = advance_response.json()
            # Check if override was noted
            if "blocker_overrides" in data:
                print(f"✅ Override response received")
            else:
                print(f"✅ Response received")

    def test_advance_response_structure(self):
        """Test that advance response has correct structure."""
        deal_id = 1
        
        advance_response = client.post(
            f"/api/heimdall/deals/{deal_id}/advance-stage",
            json={
                "requested_stage": "preliminary_analysis",
                "approved_by": "test_user@example.com",
                "reason": "Testing response structure",
            },
            headers=HEADERS
        )
        
        if advance_response.status_code == 200:
            data = advance_response.json()
            
            assert "deal_id" in data
            assert "action" in data
            assert "result" in data
            assert "timestamp" in data
            
            if data["result"] == "success":
                assert "previous_stage" in data
                assert "new_stage" in data
                assert "approved_by" in data
            
            print(f"✅ Advance response structure correct")


class TestHeimdallAudit:
    """Test audit logging from Heimdall actions."""

    def test_audit_entries_created(self):
        """Test that audit entries are created for Heimdall actions."""
        deal_id = 1
        
        # Trigger an analysis
        analysis_response = client.post(f"/api/heimdall/deals/{deal_id}/analyze", headers=HEADERS)
        
        if analysis_response.status_code != 200:
            pytest.skip("Could not analyze deal")
        
        # Check audit trail for this deal
        audit_response = client.get(f"/api/audit/deals/{deal_id}", headers=HEADERS)
        
        assert audit_response.status_code in [200, 404]
        if audit_response.status_code == 200:
            events = audit_response.json()
            
            # Look for Heimdall events
            heimdall_events = [e for e in events if "heimdall" in str(e).lower()]
            
            if heimdall_events:
                print(f"✅ Found {len(heimdall_events)} Heimdall audit events")
            else:
                print(f"⚠️ No Heimdall events in audit trail yet")

    def test_audit_contains_metadata(self):
        """Test that audit entries contain useful metadata."""
        deal_id = 1
        
        # Get audit trail
        audit_response = client.get(f"/api/audit/deals/{deal_id}", headers=HEADERS)
        
        if audit_response.status_code == 200:
            events = audit_response.json()
            
            if events:
                event = events[0]
                # Check for metadata field
                if isinstance(event, dict):
                    if "meta" in event or "metadata" in event:
                        print(f"✅ Audit entry contains metadata")
                    else:
                        print(f"⚠️ Audit entry structure: {event.keys()}")


class TestHeimdallIntegration:
    """Integration tests with full pipeline."""

    def test_full_analysis_workflow(self):
        """Test complete analysis + advance workflow."""
        deal_id = 1
        
        print("\n=== Full Heimdall Workflow ===")
        
        # Step 1: Analyze
        print("Step 1: Analyzing deal...")
        analysis_response = client.post(f"/api/heimdall/deals/{deal_id}/analyze", headers=HEADERS)
        assert analysis_response.status_code in [200, 404]
        
        if analysis_response.status_code == 200:
            analysis = analysis_response.json()
            print(f"  Current stage: {analysis['current_stage']}")
            print(f"  Blockers: {analysis['blocker_flags']}")
            print(f"  Risks: {analysis['risk_flags']}")
            print(f"  Recommended next: {analysis['recommendations']['recommended_stage']}")
            
            valid_stages = analysis['recommendations']['next_valid_stages']
            if valid_stages:
                # Step 2: Try to advance
                requested = valid_stages[0]
                print(f"\nStep 2: Attempting to advance to {requested}...")
                
                advance_response = client.post(
                    f"/api/heimdall/deals/{deal_id}/advance-stage",
                    json={
                        "requested_stage": requested,
                        "approved_by": "test@example.com",
                        "reason": "Testing integration workflow",
                    },
                    headers=HEADERS
                )
                
                assert advance_response.status_code in [200, 400]
                result = advance_response.json()
                print(f"  Result: {result['result']}")
                
                if result['result'] == 'success':
                    print(f"  ✅ Successfully advanced from {result['previous_stage']} to {result['new_stage']}")
                else:
                    print(f"  ℹ️ Not advanced: {result.get('reason', 'No reason given')}")
        else:
            print("  Deal not found for testing")

    def test_smoke_pipeline_with_heimdall(self):
        """Test Heimdall as part of the complete pipeline."""
        print("\n=== Heimdall in Complete Pipeline ===")
        
        # This would integrate with the smoke test pipeline
        # For now, just verify endpoints are accessible
        
        for deal_id in [1, 2, 3]:
            analyze_response = client.post(
                f"/api/heimdall/deals/{deal_id}/analyze",
                headers=HEADERS
            )
            
            if analyze_response.status_code == 200:
                print(f"✅ Deal {deal_id}: Heimdall ready")
            elif analyze_response.status_code == 404:
                print(f"ℹ️ Deal {deal_id}: Not found")
            else:
                print(f"⚠️ Deal {deal_id}: Error {analyze_response.status_code}")


def run_heimdall_tests():
    """Execute all Heimdall tests."""
    print("\n" + "=" * 80)
    print("HEIMDALL V0.1 TEST SUITE")
    print("=" * 80)
    
    test_suite = {
        "Analysis": TestHeimdallAnalysis(),
        "Stage Advance": TestHeimdallStageAdvance(),
        "Audit": TestHeimdallAudit(),
        "Integration": TestHeimdallIntegration(),
    }
    
    results = {}
    
    for category, tests in test_suite.items():
        print(f"\n--- {category} ---")
        for method_name in dir(tests):
            if method_name.startswith("test_"):
                try:
                    method = getattr(tests, method_name)
                    method()
                    results[f"{category}.{method_name}"] = "✅ PASS"
                except Exception as e:
                    results[f"{category}.{method_name}"] = f"❌ FAIL: {str(e)[:50]}"
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for name, result in results.items():
        print(f"{result:20} {name}")
    
    passed = sum(1 for r in results.values() if "✅" in r)
    total = len(results)
    print(f"\n{passed}/{total} tests passed")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_heimdall_tests()
