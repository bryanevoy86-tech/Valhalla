# services/api/app/tests/test_governance_decisions.py

"""
Tests for PACK R: Governance Integration
Leadership decision tracking (King, Queen, Odin, Loki, Tyr)
"""

import pytest
from fastapi.testclient import TestClient


def test_create_governance_decision(client: TestClient):
    """Test creating a new governance decision."""
    payload = {
        "subject_type": "deal",
        "subject_id": 1,
        "role": "King",
        "action": "approve",
        "reason": "Meets all criteria",
        "is_final": True
    }
    res = client.post("/governance/decisions/", json=payload)
    assert res.status_code == 201
    body = res.json()
    assert body["subject_type"] == "deal"
    assert body["subject_id"] == 1
    assert body["role"] == "King"
    assert body["action"] == "approve"
    assert body["is_final"] is True
    assert "id" in body
    assert "created_at" in body


def test_get_decision_by_id(client: TestClient):
    """Test retrieving a specific decision by ID."""
    # Create a decision first
    payload = {
        "subject_type": "contract",
        "subject_id": 42,
        "role": "Queen",
        "action": "deny",
        "reason": "Insufficient documentation"
    }
    create_res = client.post("/governance/decisions/", json=payload)
    decision_id = create_res.json()["id"]
    
    # Get it back
    res = client.get(f"/governance/decisions/{decision_id}")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == decision_id
    assert body["role"] == "Queen"


def test_get_nonexistent_decision(client: TestClient):
    """Test that getting a nonexistent decision returns 404."""
    res = client.get("/governance/decisions/999999")
    assert res.status_code == 404


def test_list_governance_decisions_for_subject(client: TestClient):
    """Test listing all decisions for a specific subject."""
    # Create multiple decisions for same subject
    for i, role in enumerate(["Odin", "Loki", "Tyr"]):
        payload = {
            "subject_type": "deal",
            "subject_id": 100,
            "role": role,
            "action": "approve" if i % 2 == 0 else "flag",
            "reason": f"Decision by {role}"
        }
        client.post("/governance/decisions/", json=payload)
    
    # List them
    res = client.get("/governance/decisions/subject/deal/100")
    assert res.status_code == 200
    decisions = res.json()
    assert isinstance(decisions, list)
    assert len(decisions) >= 3


def test_get_latest_final_decision(client: TestClient):
    """Test getting the most recent final decision for a subject."""
    subject_id = 200
    
    # Create non-final decision
    client.post("/governance/decisions/", json={
        "subject_type": "professional",
        "subject_id": subject_id,
        "role": "Loki",
        "action": "flag",
        "is_final": False
    })
    
    # Create final decision
    final_payload = {
        "subject_type": "professional",
        "subject_id": subject_id,
        "role": "King",
        "action": "approve",
        "reason": "Final approval",
        "is_final": True
    }
    client.post("/governance/decisions/", json=final_payload)
    
    # Get latest final
    res = client.get(f"/governance/decisions/subject/professional/{subject_id}/latest-final")
    assert res.status_code == 200
    body = res.json()
    assert body is not None
    assert body["is_final"] is True
    assert body["role"] == "King"


def test_list_decisions_by_role(client: TestClient):
    """Test filtering decisions by governance role."""
    # Create decisions by different roles
    roles = ["King", "Queen", "Odin"]
    for role in roles:
        client.post("/governance/decisions/", json={
            "subject_type": "deal",
            "subject_id": 300,
            "role": role,
            "action": "approve"
        })
    
    # Get King's decisions
    res = client.get("/governance/decisions/by-role/King")
    assert res.status_code == 200
    decisions = res.json()
    assert isinstance(decisions, list)
    # All should be King's
    for dec in decisions:
        assert dec["role"] == "King"


def test_decision_action_types(client: TestClient):
    """Test all supported action types."""
    actions = ["approve", "deny", "override", "flag"]
    
    for action in actions:
        payload = {
            "subject_type": "contract",
            "subject_id": 400,
            "role": "Tyr",
            "action": action,
            "reason": f"Testing {action} action"
        }
        res = client.post("/governance/decisions/", json=payload)
        assert res.status_code == 201
        assert res.json()["action"] == action


def test_governance_roles(client: TestClient):
    """Test all governance roles."""
    roles = ["King", "Queen", "Odin", "Loki", "Tyr"]
    
    for role in roles:
        payload = {
            "subject_type": "deal",
            "subject_id": 500,
            "role": role,
            "action": "approve",
            "reason": f"{role} decision"
        }
        res = client.post("/governance/decisions/", json=payload)
        assert res.status_code == 201
        assert res.json()["role"] == role
