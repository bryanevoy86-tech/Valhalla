"""
Test suite for PACK R — Governance Integration
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def governance_payload():
    return {
        "subject_type": "deal",
        "subject_id": 1,
        "role": "King",
        "action": "approve",
        "reason": "Meets all Valhalla criteria",
        "is_final": True,
    }


def test_create_governance_decision(client, governance_payload):
    """Test creating a governance decision."""
    res = client.post("/governance/decisions/", json=governance_payload)
    assert res.status_code == 201
    body = res.json()
    assert body["subject_type"] == "deal"
    assert body["subject_id"] == 1
    assert body["role"] == "King"
    assert body["action"] == "approve"
    assert body["is_final"] is True


def test_list_decisions_for_subject(client, governance_payload):
    """Test listing decisions for a subject."""
    # Create a decision first
    res1 = client.post("/governance/decisions/", json=governance_payload)
    assert res1.status_code == 201

    # List decisions for that subject
    res2 = client.get("/governance/decisions/subject/deal/1")
    assert res2.status_code == 200
    body = res2.json()
    assert isinstance(body, list)
    assert len(body) >= 1


def test_get_decision_by_id(client, governance_payload):
    """Test getting a specific decision by ID."""
    # Create a decision
    res1 = client.post("/governance/decisions/", json=governance_payload)
    assert res1.status_code == 201
    decision_id = res1.json()["id"]

    # Get the decision by ID
    res2 = client.get(f"/governance/decisions/{decision_id}")
    assert res2.status_code == 200
    body = res2.json()
    assert body["id"] == decision_id
    assert body["role"] == "King"


def test_get_latest_final_decision(client, governance_payload):
    """Test getting the latest final decision for a subject."""
    # Create a decision
    res1 = client.post("/governance/decisions/", json=governance_payload)
    assert res1.status_code == 201

    # Get the latest final decision
    res2 = client.get("/governance/decisions/subject/deal/1/latest-final")
    assert res2.status_code == 200
    body = res2.json()
    assert body["is_final"] is True
    assert body["role"] == "King"


def test_list_decisions_by_role(client, governance_payload):
    """Test listing decisions by a specific role."""
    # Create a decision by King
    res1 = client.post("/governance/decisions/", json=governance_payload)
    assert res1.status_code == 201

    # List decisions by King
    res2 = client.get("/governance/decisions/by-role/King")
    assert res2.status_code == 200
    body = res2.json()
    assert isinstance(body, list)
    assert len(body) >= 1


def test_multiple_roles(client):
    """Test decisions from multiple roles."""
    # King decision
    king_payload = {
        "subject_type": "deal",
        "subject_id": 2,
        "role": "King",
        "action": "approve",
        "reason": "Good deal",
        "is_final": False,
    }
    res1 = client.post("/governance/decisions/", json=king_payload)
    assert res1.status_code == 201

    # Queen decision
    queen_payload = {
        "subject_type": "deal",
        "subject_id": 2,
        "role": "Queen",
        "action": "deny",
        "reason": "Not aligned",
        "is_final": False,
    }
    res2 = client.post("/governance/decisions/", json=queen_payload)
    assert res2.status_code == 201

    # List all decisions for subject
    res3 = client.get("/governance/decisions/subject/deal/2")
    assert res3.status_code == 200
    body = res3.json()
    assert len(body) == 2
    roles = {d["role"] for d in body}
    assert "King" in roles
    assert "Queen" in roles


def test_governance_decision_without_reason(client):
    """Test creating a decision without a reason."""
    payload = {
        "subject_type": "contract",
        "subject_id": 5,
        "role": "Odin",
        "action": "override",
        "reason": None,
        "is_final": True,
    }
    res = client.post("/governance/decisions/", json=payload)
    assert res.status_code == 201
    body = res.json()
    assert body["reason"] is None


def test_all_governance_roles(client):
    """Test all standard governance roles."""
    roles = ["King", "Queen", "Odin", "Loki", "Tyr"]
    subject_id = 10

    for idx, role in enumerate(roles):
        payload = {
            "subject_type": "professional",
            "subject_id": subject_id,
            "role": role,
            "action": "approve",
            "reason": f"{role} approves",
            "is_final": False,
        }
        res = client.post("/governance/decisions/", json=payload)
        assert res.status_code == 201
        body = res.json()
        assert body["role"] == role

    # Verify all roles in list
    res_list = client.get(f"/governance/decisions/subject/professional/{subject_id}")
    assert res_list.status_code == 200
    body_list = res_list.json()
    assert len(body_list) == 5


def test_all_governance_actions(client):
    """Test all standard governance actions."""
    actions = ["approve", "deny", "override", "flag"]

    for idx, action in enumerate(actions):
        payload = {
            "subject_type": "deal",
            "subject_id": 20 + idx,
            "role": "King",
            "action": action,
            "reason": f"Testing {action}",
            "is_final": False,
        }
        res = client.post("/governance/decisions/", json=payload)
        assert res.status_code == 201
        body = res.json()
        assert body["action"] == action


def test_subject_type_flexibility(client):
    """Test that subject_type is flexible for any entity type."""
    subject_types = ["deal", "contract", "professional", "custom_entity"]

    for idx, subject_type in enumerate(subject_types):
        payload = {
            "subject_type": subject_type,
            "subject_id": 100 + idx,
            "role": "King",
            "action": "approve",
            "reason": f"Decision on {subject_type}",
            "is_final": False,
        }
        res = client.post("/governance/decisions/", json=payload)
        assert res.status_code == 201
        body = res.json()
        assert body["subject_type"] == subject_type
