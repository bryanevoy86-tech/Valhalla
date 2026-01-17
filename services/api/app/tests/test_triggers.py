"""
PACK CI6: Trigger & Threshold Engine Test Suite
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_create_trigger_rule(client):
    """Test creating a trigger rule."""
    response = client.post("/intelligence/triggers/rules", json={
        "name": "daily_cash_check",
        "category": "cash_management",
        "description": "Check daily cash balance",
        "condition": {
            "type": "threshold",
            "variable": "cash_balance",
            "operator": "less_than",
            "value": 50000,
        },
        "action": {
            "type": "notify",
            "channel": "slack",
            "message": "Low cash balance alert",
        },
        "active": True,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "daily_cash_check"


def test_upsert_trigger_rule(client):
    """Test updating a trigger rule by name (idempotent)."""
    client.post("/intelligence/triggers/rules", json={
        "name": "portfolio_check",
        "category": "portfolio",
        "description": "Initial check",
        "condition": {"type": "threshold"},
        "action": {"type": "notify"},
    })
    
    response = client.post("/intelligence/triggers/rules", json={
        "name": "portfolio_check",
        "category": "portfolio",
        "description": "Updated check",
        "condition": {"type": "threshold"},
        "action": {"type": "notify"},
    })
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated check"


def test_list_trigger_rules(client):
    """Test listing all trigger rules."""
    for i in range(3):
        client.post("/intelligence/triggers/rules", json={
            "name": f"rule_{i}",
            "category": "test",
            "description": f"Rule {i}",
            "condition": {"type": "threshold"},
            "action": {"type": "notify"},
        })
    
    response = client.get("/intelligence/triggers/rules")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_trigger_with_complex_condition(client):
    """Test trigger with complex condition logic."""
    response = client.post("/intelligence/triggers/rules", json={
        "name": "complex_condition",
        "category": "compound",
        "description": "Complex AND condition",
        "condition": {
            "type": "and",
            "conditions": [
                {"variable": "cash_balance", "operator": "less_than", "value": 50000},
                {"variable": "portfolio_value", "operator": "less_than", "value": 500000},
            ],
        },
        "action": {"type": "escalate"},
    })
    assert response.status_code == 200


def test_evaluate_trigger(client):
    """Test evaluating a trigger."""
    rule_resp = client.post("/intelligence/triggers/rules", json={
        "name": "test_eval",
        "category": "test",
        "condition": {"type": "threshold"},
        "action": {"type": "notify"},
    })
    rule_id = rule_resp.json()["id"]
    
    response = client.post("/intelligence/triggers/evaluate", json={
        "rule_id": rule_id,
        "context": {"cash_balance": 30000},
    })
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_list_trigger_events(client):
    """Test listing trigger events."""
    response = client.get("/intelligence/triggers/events")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_trigger_event_with_detailed_context(client):
    """Test trigger event with rich context."""
    rule_resp = client.post("/intelligence/triggers/rules", json={
        "name": "context_test",
        "category": "test",
        "condition": {"type": "threshold"},
        "action": {"type": "notify"},
    })
    rule_id = rule_resp.json()["id"]
    
    response = client.post("/intelligence/triggers/evaluate", json={
        "rule_id": rule_id,
        "context": {
            "cash_balance": 30000,
            "portfolio_value": 400000,
            "timestamp": "2024-01-15T10:30:00Z",
            "triggered_by": "system_scan",
        },
    })
    assert response.status_code == 200
