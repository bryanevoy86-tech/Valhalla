"""
PACK UB: Deployment Profile Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_deployment_profile(client):
    """Test deployment profile endpoint"""
    res = client.get("/system/deploy/profile?environment=dev")
    assert res.status_code == 200
    body = res.json()
    assert "environment" in body
    assert "version" in body
    assert "timestamp" in body
    assert body["environment"] == "dev"


def test_deployment_profile_stage(client):
    """Test deployment profile for stage"""
    res = client.get("/system/deploy/profile?environment=stage")
    assert res.status_code == 200
    body = res.json()
    assert body["environment"] == "stage"


def test_deployment_profile_prod(client):
    """Test deployment profile for prod"""
    res = client.get("/system/deploy/profile?environment=prod")
    assert res.status_code == 200
    body = res.json()
    assert body["environment"] == "prod"
    assert "version" in body
