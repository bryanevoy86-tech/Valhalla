"""
PACK TZ: System Config CRUD Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_system_config_crud(client):
    """Test create and retrieve config"""
    s = client.post(
        "/system/config/",
        json={"key": "env", "value": "dev", "description": "Environment"},
    )
    assert s.status_code == 200
    assert s.json()["key"] == "env"
    assert s.json()["value"] == "dev"


def test_system_config_get_single(client):
    """Test get single config by key"""
    client.post(
        "/system/config/",
        json={"key": "test_key", "value": "test_value"},
    )
    r = client.get("/system/config/test_key")
    assert r.status_code == 200
    assert r.json()["value"] == "test_value"


def test_system_config_list(client):
    """Test list all configs"""
    client.post(
        "/system/config/",
        json={"key": "key1", "value": "value1"},
    )
    r = client.get("/system/config/")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body
    assert "items" in body
    assert isinstance(body["items"], list)


def test_system_config_not_found(client):
    """Test 404 for non-existent key"""
    r = client.get("/system/config/nonexistent")
    assert r.status_code == 404


def test_system_config_immutable(client):
    """Test that immutable configs cannot be changed"""
    client.post(
        "/system/config/",
        json={"key": "immutable_key", "value": "original", "mutable": False},
    )
    client.post(
        "/system/config/",
        json={"key": "immutable_key", "value": "changed", "mutable": False},
    )
    r = client.get("/system/config/immutable_key")
    assert r.json()["value"] == "original"
