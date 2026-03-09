"""
PACK AQ: Workflow Guardrails Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import get_db
from app.models.base import Base


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_rule():
    payload = {
        "entity_type": "deal",
        "action": "update_stage",
        "role": "king",
        "is_allowed": True,
    }
    res = client.post("/workflow/guardrails/rules", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["entity_type"] == "deal"
    assert body["is_allowed"] is True


def test_list_rules():
    for i in range(3):
        client.post(
            "/workflow/guardrails/rules",
            json={
                "entity_type": "deal",
                "action": f"action_{i}",
                "role": "king",
            },
        )

    res = client.get("/workflow/guardrails/rules")
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 3


def test_list_rules_by_entity_type():
    # Create rules for different entity types
    client.post(
        "/workflow/guardrails/rules",
        json={
            "entity_type": "deal",
            "action": "create",
            "role": "king",
        },
    )
    client.post(
        "/workflow/guardrails/rules",
        json={
            "entity_type": "contract",
            "action": "create",
            "role": "queen",
        },
    )

    res = client.get("/workflow/guardrails/rules", params={"entity_type": "deal"})
    assert res.status_code == 200
    body = res.json()
    assert all(r["entity_type"] == "deal" for r in body)


def test_check_action_allowed():
    # Create rule allowing action
    client.post(
        "/workflow/guardrails/rules",
        json={
            "entity_type": "deal",
            "action": "update_stage",
            "role": "king",
            "is_allowed": True,
        },
    )

    res = client.get(
        "/workflow/guardrails/check",
        params={"entity_type": "deal", "action": "update_stage", "role": "king"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["allowed"] is True


def test_check_action_denied():
    # Create deny rule
    client.post(
        "/workflow/guardrails/rules",
        json={
            "entity_type": "contract",
            "action": "delete",
            "role": "va",
            "is_allowed": False,
        },
    )

    res = client.get(
        "/workflow/guardrails/check",
        params={"entity_type": "contract", "action": "delete", "role": "va"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["allowed"] is False


def test_check_action_no_rule():
    """No rule means action is not allowed by default."""
    res = client.get(
        "/workflow/guardrails/check",
        params={"entity_type": "unknown", "action": "unknown", "role": "unknown"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["allowed"] is False


def test_record_violation():
    res = client.post(
        "/workflow/guardrails/violations",
        params={
            "entity_type": "deal",
            "action": "update_stage",
            "actor": "user_123",
            "entity_id": "deal_456",
            "actor_role": "va",
            "reason": "Unauthorized attempt",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["entity_type"] == "deal"
    assert body["actor"] == "user_123"


def test_list_violations():
    # Record multiple violations
    for i in range(3):
        client.post(
            "/workflow/guardrails/violations",
            params={
                "entity_type": "deal",
                "action": f"action_{i}",
                "actor": f"user_{i}",
                "reason": f"Violation {i}",
            },
        )

    res = client.get("/workflow/guardrails/violations")
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 3


def test_update_rule():
    # Create rule
    res = client.post(
        "/workflow/guardrails/rules",
        json={
            "entity_type": "deal",
            "action": "close",
            "role": "king",
            "is_allowed": True,
        },
    )
    rule_id = res.json()["id"]

    # Update rule
    update_res = client.patch(
        f"/workflow/guardrails/rules/{rule_id}",
        json={"is_allowed": False},
    )
    assert update_res.status_code == 200
    body = update_res.json()
    assert body["is_allowed"] is False


def test_deny_wins_over_allow():
    """When both allow and deny rules exist, deny should win."""
    # Create allow rule
    client.post(
        "/workflow/guardrails/rules",
        json={
            "entity_type": "deal",
            "action": "update",
            "role": "contractor",
            "is_allowed": True,
        },
    )
    # Create deny rule for same entity/action/role
    client.post(
        "/workflow/guardrails/rules",
        json={
            "entity_type": "deal",
            "action": "update",
            "role": "contractor",
            "is_allowed": False,
        },
    )

    res = client.get(
        "/workflow/guardrails/check",
        params={"entity_type": "deal", "action": "update", "role": "contractor"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["allowed"] is False
