"""
PACK AP: Decision Governance Tests
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


def test_create_policy():
    payload = {
        "key": "approve_deal",
        "name": "Approve Deal",
        "description": "Policy for approving deals",
        "allowed_roles": "king,queen",
        "min_approvals": 2,
    }
    res = client.post("/governance/decisions/policies", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["key"] == "approve_deal"
    assert body["min_approvals"] == 2
    assert body["is_active"] is True


def test_list_policies():
    client.post(
        "/governance/decisions/policies",
        json={"key": "policy1", "name": "Policy 1"},
    )
    client.post(
        "/governance/decisions/policies",
        json={"key": "policy2", "name": "Policy 2"},
    )

    res = client.get("/governance/decisions/policies")
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 2


def test_get_policy_by_key():
    client.post(
        "/governance/decisions/policies",
        json={"key": "test_policy", "name": "Test Policy"},
    )

    res = client.get("/governance/decisions/policies/test_policy")
    assert res.status_code == 200
    body = res.json()
    assert body["key"] == "test_policy"


def test_get_nonexistent_policy():
    res = client.get("/governance/decisions/policies/nonexistent")
    assert res.status_code == 404


def test_create_policy_and_decision():
    # Create policy
    p_res = client.post(
        "/governance/decisions/policies",
        json={"key": "approve_deal", "name": "Approve Deal"},
    )
    assert p_res.status_code == 200

    # Create decision
    d_res = client.post(
        "/governance/decisions/",
        json={
            "policy_key": "approve_deal",
            "entity_type": "deal",
            "entity_id": "deal_123",
            "initiator": "king",
            "initiator_role": "king",
        },
    )
    assert d_res.status_code == 200
    body = d_res.json()
    assert body["status"] == "pending"
    assert body["policy_key"] == "approve_deal"


def test_update_decision_approval():
    # Create policy and decision
    client.post(
        "/governance/decisions/policies",
        json={"key": "approve_deal", "name": "Approve Deal"},
    )
    d_res = client.post(
        "/governance/decisions/",
        json={
            "policy_key": "approve_deal",
            "entity_type": "deal",
            "entity_id": "deal_456",
            "initiator": "user1",
        },
    )
    decision_id = d_res.json()["id"]

    # Update to approved
    update_res = client.patch(
        f"/governance/decisions/{decision_id}",
        json={"status": "approved"},
    )
    assert update_res.status_code == 200
    body = update_res.json()
    assert body["status"] == "approved"
    assert body["decided_at"] is not None


def test_list_decisions_for_entity():
    # Create policy
    client.post(
        "/governance/decisions/policies",
        json={"key": "test_policy", "name": "Test"},
    )

    # Create multiple decisions for same entity
    for i in range(3):
        client.post(
            "/governance/decisions/",
            json={
                "policy_key": "test_policy",
                "entity_type": "deal",
                "entity_id": "deal_789",
                "initiator": f"user_{i}",
            },
        )

    res = client.get(
        "/governance/decisions/by-entity",
        params={"entity_type": "deal", "entity_id": "deal_789"},
    )
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 3


def test_decision_with_context():
    client.post(
        "/governance/decisions/policies",
        json={"key": "policy_ctx", "name": "Policy with Context"},
    )

    payload = {
        "policy_key": "policy_ctx",
        "entity_type": "contract",
        "entity_id": "contract_001",
        "initiator": "legal_team",
        "context": {"amount": 50000, "term_months": 12},
    }
    res = client.post("/governance/decisions/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["context"]["amount"] == 50000
    assert body["context"]["term_months"] == 12
