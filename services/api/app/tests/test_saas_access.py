"""
PACK AD: SaaS Access Engine Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.core.db import get_db
from app.models.base import Base


@pytest.fixture
def db():
    """In-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def client(db: Session):
    """FastAPI test client with in-memory database"""
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_saas_plan(client):
    """Test creating a new SaaS plan with modules"""
    payload = {
        "code": "VALHALLA_PRO",
        "name": "Valhalla Pro",
        "description": "Professional plan with wholesale engine",
        "price_monthly": 97.0,
        "price_yearly": 970.0,
        "currency": "USD",
        "modules": [
            {"module_key": "wholesale_engine"},
            {"module_key": "dispo_engine"},
        ],
    }
    res = client.post("/saas/plans", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["code"] == "VALHALLA_PRO"
    assert data["name"] == "Valhalla Pro"
    assert len(data["modules"]) == 2
    assert data["is_active"] is True


def test_list_saas_plans(client):
    """Test listing all active SaaS plans"""
    # Create a plan first
    payload = {
        "code": "VALHALLA_FREE",
        "name": "Valhalla Free",
        "price_monthly": 0.0,
        "modules": [],
    }
    client.post("/saas/plans", json=payload)

    # List plans
    res = client.get("/saas/plans")
    assert res.status_code == 200
    plans = res.json()
    assert len(plans) >= 1
    assert any(p["code"] == "VALHALLA_FREE" for p in plans)


def test_get_saas_plan(client):
    """Test getting a specific SaaS plan"""
    # Create a plan
    payload = {
        "code": "VALHALLA_EMPIRE",
        "name": "Valhalla Empire",
        "price_monthly": 197.0,
        "modules": [{"module_key": "empire_engine"}],
    }
    res = client.post("/saas/plans", json=payload)
    plan_id = res.json()["id"]

    # Get the plan
    res = client.get(f"/saas/plans/{plan_id}")
    assert res.status_code == 200
    assert res.json()["code"] == "VALHALLA_EMPIRE"


def test_get_nonexistent_plan(client):
    """Test getting a non-existent plan returns 404"""
    res = client.get("/saas/plans/999")
    assert res.status_code == 404


def test_update_saas_plan(client):
    """Test updating a SaaS plan"""
    # Create a plan
    payload = {
        "code": "VALHALLA_PRO",
        "name": "Valhalla Pro",
        "price_monthly": 97.0,
        "modules": [],
    }
    res = client.post("/saas/plans", json=payload)
    plan_id = res.json()["id"]

    # Update the plan
    update_payload = {
        "price_monthly": 127.0,
        "name": "Valhalla Pro Plus",
    }
    res = client.patch(f"/saas/plans/{plan_id}", json=update_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["price_monthly"] == 127.0
    assert data["name"] == "Valhalla Pro Plus"


def test_create_subscription(client):
    """Test creating a subscription"""
    # Create a plan first
    plan_payload = {
        "code": "VALHALLA_PRO",
        "name": "Valhalla Pro",
        "price_monthly": 97.0,
        "modules": [{"module_key": "wholesale_engine"}],
    }
    res = client.post("/saas/plans", json=plan_payload)
    plan_id = res.json()["id"]

    # Create a subscription
    sub_payload = {
        "user_id": 1,
        "plan_id": plan_id,
        "provider": "stripe",
        "provider_sub_id": "sub_123",
    }
    res = client.post("/saas/subscriptions", json=sub_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == 1
    assert data["status"] == "active"


def test_update_subscription_status(client):
    """Test updating subscription status"""
    # Create plan and subscription
    plan_payload = {
        "code": "VALHALLA_PRO",
        "name": "Valhalla Pro",
        "modules": [],
    }
    res = client.post("/saas/plans", json=plan_payload)
    plan_id = res.json()["id"]

    sub_payload = {"user_id": 1, "plan_id": plan_id}
    res = client.post("/saas/subscriptions", json=sub_payload)
    sub_id = res.json()["id"]

    # Update status to cancelled
    update_payload = {"status": "cancelled"}
    res = client.patch(f"/saas/subscriptions/{sub_id}", json=update_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "cancelled"
    assert data["cancelled_at"] is not None


def test_get_active_subscription_for_user(client):
    """Test getting active subscription for a user"""
    # Create plan and subscription
    plan_payload = {
        "code": "VALHALLA_PRO",
        "name": "Valhalla Pro",
        "modules": [],
    }
    res = client.post("/saas/plans", json=plan_payload)
    plan_id = res.json()["id"]

    sub_payload = {"user_id": 42, "plan_id": plan_id}
    client.post("/saas/subscriptions", json=sub_payload)

    # Get active subscription
    res = client.get("/saas/subscriptions/active/42")
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == 42
    assert data["status"] == "active"


def test_access_check_with_access(client):
    """Test access check returns true when user has module access"""
    # Create plan with module
    plan_payload = {
        "code": "VALHALLA_PRO",
        "name": "Valhalla Pro",
        "modules": [{"module_key": "wholesale_engine"}],
    }
    res = client.post("/saas/plans", json=plan_payload)
    plan_id = res.json()["id"]

    # Create subscription
    sub_payload = {"user_id": 10, "plan_id": plan_id}
    client.post("/saas/subscriptions", json=sub_payload)

    # Check access
    res = client.get("/saas/access-check", params={"user_id": 10, "module_key": "wholesale_engine"})
    assert res.status_code == 200
    data = res.json()
    assert data["has_access"] is True
    assert data["plan_code"] == "VALHALLA_PRO"


def test_access_check_without_access(client):
    """Test access check returns false for unauthorized module"""
    # Create plan without module
    plan_payload = {
        "code": "VALHALLA_FREE",
        "name": "Valhalla Free",
        "modules": [],
    }
    res = client.post("/saas/plans", json=plan_payload)
    plan_id = res.json()["id"]

    # Create subscription
    sub_payload = {"user_id": 11, "plan_id": plan_id}
    client.post("/saas/subscriptions", json=sub_payload)

    # Check access to unauthorized module
    res = client.get("/saas/access-check", params={"user_id": 11, "module_key": "wholesale_engine"})
    assert res.status_code == 200
    data = res.json()
    assert data["has_access"] is False
