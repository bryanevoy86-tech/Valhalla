import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json().get("status") == "ok"


def test_auth_login(client):
    r = client.post("/auth/login", json={"email": "admin@valhalla", "password": "adminpass"})
    assert r.status_code == 200 and "access_token" in r.json()


def test_jobs_summary(client):
    token = "dummy-token"  # Replace with real token logic if available
    r = client.get("/jobs/summary", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
