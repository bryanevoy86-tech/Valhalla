# services/api/app/tests/test_deploy_check.py

"""
Tests for PACK V: Deployment Checklist / Ops Automation
Verifies deployment readiness check endpoint functionality.
"""

from __future__ import annotations

import pytest
import os
from fastapi.testclient import TestClient


def test_deploy_check_endpoint_exists(client: TestClient):
    """Test that /ops/deploy-check/ endpoint exists."""
    res = client.get("/ops/deploy-check/")
    assert res.status_code == 200


def test_deploy_check_response_structure(client: TestClient):
    """Test that deploy check response has the expected structure."""
    res = client.get("/ops/deploy-check/")
    assert res.status_code == 200
    
    body = res.json()
    assert "timestamp" in body
    assert "overall_ok" in body
    assert "checks" in body


def test_deploy_check_timestamp_present(client: TestClient):
    """Test that timestamp is present and valid ISO 8601."""
    res = client.get("/ops/deploy-check/")
    body = res.json()
    
    timestamp = body["timestamp"]
    assert isinstance(timestamp, str)
    # Should be ISO 8601 format
    assert "T" in timestamp or "-" in timestamp


def test_deploy_check_overall_ok_is_boolean(client: TestClient):
    """Test that overall_ok is a boolean."""
    res = client.get("/ops/deploy-check/")
    body = res.json()
    
    assert isinstance(body["overall_ok"], bool)


def test_deploy_check_checks_structure(client: TestClient):
    """Test that checks object has all required subsections."""
    res = client.get("/ops/deploy-check/")
    body = res.json()
    
    checks = body["checks"]
    assert "environment" in checks
    assert "database" in checks
    assert "routes" in checks


def test_deploy_check_environment_check(client: TestClient):
    """Test environment variable check structure."""
    res = client.get("/ops/deploy-check/")
    body = res.json()
    
    env_check = body["checks"]["environment"]
    assert "ok" in env_check
    assert "details" in env_check
    assert isinstance(env_check["ok"], bool)
    assert isinstance(env_check["details"], dict)


def test_deploy_check_database_check(client: TestClient):
    """Test database health check structure."""
    res = client.get("/ops/deploy-check/")
    body = res.json()
    
    db_check = body["checks"]["database"]
    assert "ok" in db_check
    assert isinstance(db_check["ok"], bool)


def test_deploy_check_routes_check(client: TestClient):
    """Test routes availability check structure."""
    res = client.get("/ops/deploy-check/")
    body = res.json()
    
    routes_check = body["checks"]["routes"]
    assert "total_routes" in routes_check
    assert "required_prefixes" in routes_check
    assert "missing_prefixes" in routes_check
    assert "ok" in routes_check
    
    assert isinstance(routes_check["total_routes"], int)
    assert isinstance(routes_check["required_prefixes"], list)
    assert isinstance(routes_check["missing_prefixes"], list)
    assert isinstance(routes_check["ok"], bool)


def test_deploy_check_required_prefixes_present(client: TestClient):
    """Test that required route prefixes are listed."""
    res = client.get("/ops/deploy-check/")
    body = res.json()
    
    required = body["checks"]["routes"]["required_prefixes"]
    assert len(required) > 0
    
    # Check for critical prefixes
    assert any("/debug" in p for p in required)
    assert any("/ui-map" in p for p in required)


def test_deploy_check_total_routes_reasonable(client: TestClient):
    """Test that total route count is reasonable."""
    res = client.get("/ops/deploy-check/")
    body = res.json()
    
    total = body["checks"]["routes"]["total_routes"]
    # Should have at least a few routes
    assert total > 5


def test_deploy_check_routes_ok_if_no_missing(client: TestClient):
    """Test that routes check is OK if no prefixes are missing."""
    res = client.get("/ops/deploy-check/")
    body = res.json()
    
    routes_check = body["checks"]["routes"]
    if len(routes_check["missing_prefixes"]) == 0:
        assert routes_check["ok"] is True


def test_deploy_check_database_health(client: TestClient):
    """Test that database health check works."""
    res = client.get("/ops/deploy-check/")
    body = res.json()
    
    db_check = body["checks"]["database"]
    # Should be a boolean value
    assert db_check["ok"] in (True, False)


def test_deploy_check_multiple_calls_consistent(client: TestClient):
    """Test that multiple calls return consistent results."""
    res1 = client.get("/ops/deploy-check/")
    res2 = client.get("/ops/deploy-check/")
    
    body1 = res1.json()
    body2 = res2.json()
    
    # Core checks should be consistent
    assert body1["checks"]["environment"]["ok"] == body2["checks"]["environment"]["ok"]
    assert body1["checks"]["routes"]["ok"] == body2["checks"]["routes"]["ok"]


def test_deploy_check_readable_output(client: TestClient):
    """Test that deploy check output is human-readable."""
    res = client.get("/ops/deploy-check/")
    body = res.json()
    
    # Should be able to understand the output structure
    assert "checks" in body
    for check_name in ["environment", "database", "routes"]:
        assert check_name in body["checks"]
        assert "ok" in body["checks"][check_name]
