"""
PACK CI5: Tuning Rules Test Suite
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_create_tuning_profile(client):
    """Test creating a new tuning profile."""
    response = client.post("/intelligence/tuning/profiles", json={
        "name": "war_mode",
        "description": "Aggressive growth profile",
        "aggression": 85,
        "risk_tolerance": 70,
        "safety_bias": 40,
        "growth_bias": 90,
        "stability_bias": 30,
        "active": True,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "war_mode"
    assert data["aggression"] == 85


def test_upsert_tuning_profile_existing(client):
    """Test updating an existing profile by name (idempotent)."""
    client.post("/intelligence/tuning/profiles", json={
        "name": "default",
        "description": "Default balanced",
        "aggression": 50,
        "risk_tolerance": 50,
        "safety_bias": 70,
        "growth_bias": 70,
        "stability_bias": 60,
    })
    
    response = client.post("/intelligence/tuning/profiles", json={
        "name": "default",
        "description": "Updated default",
        "aggression": 60,
        "risk_tolerance": 60,
        "safety_bias": 65,
        "growth_bias": 75,
        "stability_bias": 65,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated default"
    assert data["aggression"] == 60


def test_list_tuning_profiles(client):
    """Test listing all tuning profiles."""
    for i in range(3):
        client.post("/intelligence/tuning/profiles", json={
            "name": f"profile_{i}",
            "aggression": 50 + i * 10,
            "risk_tolerance": 50,
            "safety_bias": 70,
            "growth_bias": 70,
            "stability_bias": 60,
        })
    
    response = client.get("/intelligence/tuning/profiles")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_profile_with_weights(client):
    """Test creating profile with custom weights."""
    response = client.post("/intelligence/tuning/profiles", json={
        "name": "custom_weights",
        "aggression": 50,
        "risk_tolerance": 50,
        "safety_bias": 70,
        "growth_bias": 70,
        "stability_bias": 60,
        "weights": {
            "deal_weight": 0.4,
            "security_weight": 0.3,
            "family_weight": 0.3,
        },
    })
    assert response.status_code == 200


def test_add_constraint(client):
    """Test adding a constraint to a profile."""
    prof_resp = client.post("/intelligence/tuning/profiles", json={
        "name": "constrained",
        "aggression": 50,
        "risk_tolerance": 50,
        "safety_bias": 70,
        "growth_bias": 70,
        "stability_bias": 60,
    })
    profile_id = prof_resp.json()["id"]
    
    response = client.post("/intelligence/tuning/constraints", json={
        "profile_id": profile_id,
        "key": "custody_risk",
        "description": "Never expose kids to risk",
        "rules": {"max_exposure": 0, "category_blacklist": ["dangerous"]},
    })
    assert response.status_code == 200


def test_list_constraints_for_profile(client):
    """Test listing constraints for a profile."""
    prof_resp = client.post("/intelligence/tuning/profiles", json={
        "name": "with_constraints",
        "aggression": 50,
        "risk_tolerance": 50,
        "safety_bias": 70,
        "growth_bias": 70,
        "stability_bias": 60,
    })
    profile_id = prof_resp.json()["id"]
    
    for i in range(2):
        client.post("/intelligence/tuning/constraints", json={
            "profile_id": profile_id,
            "key": f"constraint_{i}",
            "description": f"Constraint {i}",
        })
    
    response = client.get(f"/intelligence/tuning/profiles/{profile_id}/constraints")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data


def test_constraint_with_structured_rules(client):
    """Test constraint with complex rule structure."""
    prof_resp = client.post("/intelligence/tuning/profiles", json={
        "name": "legal",
        "aggression": 50,
        "risk_tolerance": 50,
        "safety_bias": 70,
        "growth_bias": 70,
        "stability_bias": 60,
    })
    profile_id = prof_resp.json()["id"]
    
    response = client.post("/intelligence/tuning/constraints", json={
        "profile_id": profile_id,
        "key": "legal_compliance",
        "description": "Never violate law",
        "rules": {
            "jurisdictions": ["CA", "NY"],
            "forbidden_actions": ["tax_evasion", "fraud"],
            "required_reviews": ["legal", "compliance"],
        },
    })
    assert response.status_code == 200
