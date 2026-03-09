"""
PACK CI7: Strategic Mode Engine Test Suite
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_create_strategic_mode(client):
    """Test creating a strategic mode."""
    response = client.post("/intelligence/modes/", json={
        "name": "growth_mode",
        "description": "Aggressive growth phase",
        "tuning_profile_name": "war_mode",
        "parameters": {"risk_level": "high", "capital_deployment": 0.8},
        "active": False,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "growth_mode"


def test_upsert_strategic_mode(client):
    """Test updating a strategic mode by name (idempotent)."""
    client.post("/intelligence/modes/", json={
        "name": "survival_mode",
        "description": "Initial survival",
        "tuning_profile_name": "default",
    })
    
    response = client.post("/intelligence/modes/", json={
        "name": "survival_mode",
        "description": "Updated survival",
        "tuning_profile_name": "conservative",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated survival"


def test_list_strategic_modes(client):
    """Test listing all strategic modes."""
    for i in range(3):
        client.post("/intelligence/modes/", json={
            "name": f"mode_{i}",
            "description": f"Mode {i}",
            "tuning_profile_name": f"profile_{i}",
        })
    
    response = client.get("/intelligence/modes/")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_mode_with_tuning_profile_link(client):
    """Test mode with tuning profile reference."""
    response = client.post("/intelligence/modes/", json={
        "name": "linked_mode",
        "description": "With profile link",
        "tuning_profile_name": "war_mode",
        "parameters": {"aggression": 85},
    })
    assert response.status_code == 200
    data = response.json()
    assert data["tuning_profile_name"] == "war_mode"


def test_set_active_mode(client):
    """Test setting the active mode."""
    client.post("/intelligence/modes/", json={
        "name": "active_test",
        "description": "Mode to activate",
    })
    
    response = client.post("/intelligence/modes/active", json={
        "mode_name": "active_test",
        "reason": "Switching to growth phase",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["mode_name"] == "active_test"


def test_get_active_mode(client):
    """Test retrieving the active mode."""
    client.post("/intelligence/modes/", json={
        "name": "retrieve_test",
        "description": "Mode to retrieve",
    })
    
    client.post("/intelligence/modes/active", json={
        "mode_name": "retrieve_test",
        "reason": "Testing retrieval",
    })
    
    response = client.get("/intelligence/modes/active")
    assert response.status_code == 200
    data = response.json()
    assert "mode_name" in data
    assert "changed_at" in data


def test_switch_active_mode(client):
    """Test switching between modes."""
    for mode_name in ["mode_a", "mode_b"]:
        client.post("/intelligence/modes/", json={
            "name": mode_name,
            "description": f"Test {mode_name}",
        })
    
    client.post("/intelligence/modes/active", json={
        "mode_name": "mode_a",
        "reason": "Initial",
    })
    
    response = client.post("/intelligence/modes/active", json={
        "mode_name": "mode_b",
        "reason": "Switching",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["mode_name"] == "mode_b"


def test_active_mode_default_creation(client):
    """Test default creation of active mode."""
    response = client.get("/intelligence/modes/active")
    assert response.status_code == 200
    data = response.json()
    assert "mode_name" in data or "id" in data


def test_active_mode_tracks_changes(client):
    """Test that active mode tracks change timestamps."""
    client.post("/intelligence/modes/", json={
        "name": "timestamp_test",
        "description": "Track timestamps",
    })
    
    resp1 = client.post("/intelligence/modes/active", json={
        "mode_name": "timestamp_test",
        "reason": "First",
    })
    data1 = resp1.json()
    changed_at_1 = data1.get("changed_at")
    
    assert changed_at_1 is not None
