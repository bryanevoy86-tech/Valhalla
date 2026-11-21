"""Historical CI5 profile and constraint behavior on the canonical tuning API."""

import pytest

from app.models.tuning_rules import TuningRule

ENDPOINT = "/api/v1/tuning/rules"


@pytest.fixture
def client(deal_client):
    test_client, engine = deal_client
    TuningRule.__table__.create(engine)
    return test_client


def save_profile(client, payload):
    values = dict(payload)
    record = {key: values.pop(key) for key in ("name", "description", "active") if key in values}
    return client.post(ENDPOINT, json={**record, "rule_type": "profile", "config": values})


def add_constraint(client, payload):
    return client.post(ENDPOINT, json={
        "name": payload["key"], "description": payload.get("description"),
        "rule_type": "profile_constraint",
        "config": {"profile_id": payload["profile_id"], "rules": payload.get("rules")},
    })


def test_create_tuning_profile(client):
    """Test creating a new tuning profile."""
    response = save_profile(client, {
        "name": "war_mode",
        "description": "Aggressive growth profile",
        "aggression": 85,
        "risk_tolerance": 70,
        "safety_bias": 40,
        "growth_bias": 90,
        "stability_bias": 30,
        "active": True,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "war_mode"
    assert data["config"]["aggression"] == 85


def test_upsert_tuning_profile_existing(client):
    """Test updating an existing profile by name (idempotent)."""
    initial = save_profile(client, {
        "name": "default",
        "description": "Default balanced",
        "aggression": 50,
        "risk_tolerance": 50,
        "safety_bias": 70,
        "growth_bias": 70,
        "stability_bias": 60,
    })

    response = save_profile(client, {
        "name": "default",
        "description": "Updated default",
        "aggression": 60,
        "risk_tolerance": 60,
        "safety_bias": 65,
        "growth_bias": 75,
        "stability_bias": 65,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Updated default"
    assert data["config"]["aggression"] == 60
    assert data["id"] == initial.json()["id"]
    assert client.get(ENDPOINT).json()["total"] == 1


def test_list_tuning_profiles(client):
    """Test listing all tuning profiles."""
    for i in range(3):
        save_profile(client, {
            "name": f"profile_{i}",
            "aggression": 50 + i * 10,
            "risk_tolerance": 50,
            "safety_bias": 70,
            "growth_bias": 70,
            "stability_bias": 60,
        })

    response = client.get(ENDPOINT, params={"rule_type": "profile"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert [item["name"] for item in data["items"]] == ["profile_0", "profile_1", "profile_2"]


def test_profile_with_weights(client):
    """Test creating profile with custom weights."""
    response = save_profile(client, {
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
    assert response.status_code == 201
    persisted = client.get(f"{ENDPOINT}/{response.json()['id']}").json()
    assert persisted["config"]["weights"] == {
        "deal_weight": 0.4, "security_weight": 0.3, "family_weight": 0.3,
    }


def test_add_constraint(client):
    """Test adding a constraint to a profile."""
    prof_resp = save_profile(client, {
        "name": "constrained",
        "aggression": 50,
        "risk_tolerance": 50,
        "safety_bias": 70,
        "growth_bias": 70,
        "stability_bias": 60,
    })
    profile_id = prof_resp.json()["id"]

    response = add_constraint(client, {
        "profile_id": profile_id,
        "key": "custody_risk",
        "description": "Never expose kids to risk",
        "rules": {"max_exposure": 0, "category_blacklist": ["dangerous"]},
    })
    assert response.status_code == 201
    assert response.json()["config"]["profile_id"] == profile_id
    assert client.delete(f"{ENDPOINT}/{profile_id}").status_code == 409
    assert client.post(f"{ENDPOINT}/evaluate", json={}).json() == {"passed": [], "violations": []}


def test_list_constraints_for_profile(client):
    """Test listing constraints for a profile."""
    prof_resp = save_profile(client, {
        "name": "with_constraints",
        "aggression": 50,
        "risk_tolerance": 50,
        "safety_bias": 70,
        "growth_bias": 70,
        "stability_bias": 60,
    })
    profile_id = prof_resp.json()["id"]

    for i in range(2):
        add_constraint(client, {
            "profile_id": profile_id,
            "key": f"constraint_{i}",
            "description": f"Constraint {i}",
        })

    response = client.get(ENDPOINT, params={"profile_id": profile_id})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["config"]["profile_id"] == profile_id for item in data["items"])


def test_constraint_with_structured_rules(client):
    """Test constraint with complex rule structure."""
    prof_resp = save_profile(client, {
        "name": "legal",
        "aggression": 50,
        "risk_tolerance": 50,
        "safety_bias": 70,
        "growth_bias": 70,
        "stability_bias": 60,
    })
    profile_id = prof_resp.json()["id"]

    response = add_constraint(client, {
        "profile_id": profile_id,
        "key": "legal_compliance",
        "description": "Never violate law",
        "rules": {
            "jurisdictions": ["CA", "NY"],
            "forbidden_actions": ["tax_evasion", "fraud"],
            "required_reviews": ["legal", "compliance"],
        },
    })
    assert response.status_code == 201
    constraint = client.get(f"{ENDPOINT}/{response.json()['id']}").json()
    assert constraint["config"]["rules"] == {
        "jurisdictions": ["CA", "NY"],
        "forbidden_actions": ["tax_evasion", "fraud"],
        "required_reviews": ["legal", "compliance"],
    }
    assert add_constraint(client, {"key": "missing_parent", "profile_id": profile_id + 999}).status_code == 404
    assert save_profile(client, {"name": "invalid", "risk_tolerance": 101}).status_code == 422
