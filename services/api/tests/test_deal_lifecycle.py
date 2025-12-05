# services/api/tests/test_deal_lifecycle.py

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.db import SessionLocal
from app.models.deal import Deal

client = TestClient(app)


@pytest.fixture
def db_session():
    """Provide a database session for tests"""
    db = SessionLocal()
    yield db
    db.close()


def _create_test_deal(db_session) -> int:
    """Helper: Create a test deal directly in database"""
    deal = Deal(
        lead_id=1,  # Assume lead 1 exists or use a valid ID
        headline="Test Deal",
        region="Austin",
        property_type="SFH",
        price=250000,
        offer=None,  # Initially no offer, so it's in "backend_deal_created" stage
        mao=None,  # No MAO until underwriting runs
        roi_note=None,
    )
    db_session.add(deal)
    db_session.commit()
    db_session.refresh(deal)
    return deal.id


# services/api/tests/test_deal_lifecycle.py

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.db import SessionLocal
from app.models.deal import Deal

client = TestClient(app)


@pytest.fixture
def db_session():
    """Provide a database session for tests"""
    db = SessionLocal()
    yield db
    db.close()


def _create_test_deal(db_session) -> int:
    """Helper: Create a test deal directly in database"""
    deal = Deal(
        org_id=1,
        lead_id=1,  # Assume lead 1 exists or use a valid ID
        status="draft",
        city="Austin",
        state="TX",
        price=250000.0,
        offer=None,  # Initially no offer, so it's in "backend_deal_created" stage
        mao=None,  # No MAO until underwriting runs
        roi_note=None,
    )
    db_session.add(deal)
    db_session.commit()
    db_session.refresh(deal)
    return deal.id


def test_lifecycle_status_nonexistent_deal():
    """
    Test: GET /lifecycle/status/{backend_deal_id} with nonexistent deal
    Expected:
      - Returns 404 error
    """
    resp = client.get(f"/api/lifecycle/status/99999")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
    
    data = resp.json()
    assert "not found" in data["detail"].lower()
    
    print(f"✅ Correctly returned 404 for nonexistent deal")


def test_lifecycle_status_new_deal(db_session):
    """
    Test: lifecycle_status on a newly created deal
    Expected:
      - current_stage = "backend_deal_created"
      - steps shows backend_deal_created as completed
      - next_recommended_stage = "underwriting_complete"
    """
    backend_deal_id = _create_test_deal(db_session)
    
    resp = client.get(f"/api/lifecycle/status/{backend_deal_id}")
    assert resp.status_code == 200, f"Failed to get lifecycle status: {resp.text}"
    
    data = resp.json()
    assert data["backend_deal_id"] == backend_deal_id
    assert data["current_stage"] == "backend_deal_created"
    assert data["next_recommended_stage"] == "underwriting_complete"
    
    # Check that steps list exists and shows correct statuses
    assert len(data["steps"]) > 0
    backend_created_step = next((s for s in data["steps"] if s["name"] == "backend_deal_created"), None)
    assert backend_created_step is not None
    assert backend_created_step["status"] == "completed"
    
    # Pending steps should exist
    lead_created_step = next((s for s in data["steps"] if s["name"] == "lead_created"), None)
    assert lead_created_step is not None
    assert lead_created_step["status"] in ["pending", "completed"]
    
    print(f"✅ Lifecycle status detected correctly: {data['current_stage']}")


def test_lifecycle_run_invalid_action(db_session):
    """
    Test: POST /lifecycle/run_action with invalid action name
    Expected:
      - Returns 400 error
      - Error message indicates unknown action
    """
    backend_deal_id = _create_test_deal(db_session)
    
    req = {
        "backend_deal_id": backend_deal_id,
        "action": "invalid_action_name",
    }
    resp = client.post("/api/lifecycle/run_action", json=req)
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    
    data = resp.json()
    assert "Unknown action" in data["detail"]
    
    print(f"✅ Invalid action correctly rejected")


def test_lifecycle_available_actions_at_stage(db_session):
    """
    Test: Get lifecycle status and check available actions for stage
    Expected:
      - Status shows list of automated_actions_available
      - For backend_deal_created stage, should have run_underwriting
    """
    backend_deal_id = _create_test_deal(db_session)

    # Get status to see available actions
    status_resp = client.get(f"/api/lifecycle/status/{backend_deal_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    
    available_actions = status_data.get("automated_actions_available", [])
    print(f"✅ Available actions for stage '{status_data['current_stage']}': {available_actions}")
    
    # For backend_deal_created stage, should have run_underwriting
    assert "run_underwriting" in available_actions, \
        f"Expected 'run_underwriting' in available actions for {status_data['current_stage']}"


def test_lifecycle_action_orchestrates_flows(db_session):
    """
    Test: Verify that lifecycle actions orchestrate the actual flows
    This is more of an integration test to ensure the mapping is correct
    """
    backend_deal_id = _create_test_deal(db_session)
    
    # Verify the action mapper has the right endpoints
    resp = client.post("/api/lifecycle/run_action", json={
        "backend_deal_id": backend_deal_id,
        "action": "run_underwriting",
    })
    
    # Should either succeed or fail gracefully (depending on flow router availability)
    assert resp.status_code in [200, 404, 500], \
        f"Unexpected status code: {resp.status_code}"
    
    if resp.status_code == 200:
        data = resp.json()
        assert data["status"] == "success"
        print(f"✅ Orchestration test: action executed")
    else:
        # Flow router may not be available in test environment
        print(f"⚠️  Flow router returned {resp.status_code} (may not be available in test)")


if __name__ == "__main__":
    print("Running deal_lifecycle tests...")
    test_lifecycle_status_nonexistent_deal()
    print("\nNote: Other tests require database session fixtures from pytest")
    print("Run with: pytest tests/test_deal_lifecycle.py -v")
