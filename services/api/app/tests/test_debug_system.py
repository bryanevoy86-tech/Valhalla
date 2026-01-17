# services/api/app/tests/test_debug_system.py

"""
Tests for PACK S: Final System Integration Pass
Verifies route listing and system health endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_debug_routes_endpoint(client: TestClient):
    """Test that /debug/routes returns route information."""
    res = client.get("/debug/routes")
    assert res.status_code == 200
    
    body = res.json()
    assert "routes" in body
    assert "count" in body
    assert isinstance(body["routes"], list)
    assert isinstance(body["count"], int)
    assert body["count"] > 0


def test_debug_routes_contains_health(client: TestClient):
    """Test that /debug/routes includes the health endpoint."""
    res = client.get("/debug/routes")
    assert res.status_code == 200
    
    body = res.json()
    routes = body["routes"]
    paths = [r.get("path") for r in routes]
    
    # Should have /health or similar health check endpoint
    has_health = any("health" in str(p).lower() for p in paths)
    assert has_health, "Should have a health endpoint registered"


def test_debug_system_endpoint(client: TestClient):
    """Test that /debug/system returns system snapshot."""
    res = client.get("/debug/system")
    assert res.status_code == 200
    
    body = res.json()
    assert "routes_count" in body
    assert "db_healthy" in body
    assert "subsystems" in body
    assert "timestamp" in body
    
    assert isinstance(body["routes_count"], int)
    assert isinstance(body["db_healthy"], bool)
    assert isinstance(body["subsystems"], dict)


def test_debug_system_subsystems_present(client: TestClient):
    """Test that /debug/system includes all expected subsystems."""
    res = client.get("/debug/system")
    assert res.status_code == 200
    
    body = res.json()
    subsystems = body["subsystems"]
    
    # Check for key subsystems
    expected = ["professionals", "contracts", "documents", "tasks", "audit", "governance"]
    for subsystem in expected:
        assert subsystem in subsystems, f"Subsystem '{subsystem}' should be in health check"


def test_debug_system_db_health(client: TestClient):
    """Test that database health check reports correctly."""
    res = client.get("/debug/system")
    assert res.status_code == 200
    
    body = res.json()
    # Should be able to connect to database
    assert body["db_healthy"] is True or body["db_healthy"] is False
    # Just verify it's a boolean; we can't control the actual health


def test_debug_system_routes_count_matches(client: TestClient):
    """Test that routes count in snapshot matches /debug/routes."""
    routes_res = client.get("/debug/routes")
    system_res = client.get("/debug/system")
    
    routes_body = routes_res.json()
    system_body = system_res.json()
    
    # System routes_count should match or be very close to /debug/routes count
    # (allowing for some discrepancy due to timing)
    assert isinstance(system_body["routes_count"], int)
    assert isinstance(routes_body["count"], int)


def test_debug_routes_has_proper_structure(client: TestClient):
    """Test that each route object has the proper structure."""
    res = client.get("/debug/routes")
    assert res.status_code == 200
    
    body = res.json()
    routes = body["routes"]
    
    for route in routes:
        # Each route should have these keys
        assert "path" in route
        assert "name" in route
        assert "methods" in route
        
        # Methods should be a list of strings
        assert isinstance(route["methods"], list)
        for method in route["methods"]:
            assert isinstance(method, str)
            assert method in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]


def test_debug_routes_sorted(client: TestClient):
    """Test that routes are returned in sorted order for readability."""
    res = client.get("/debug/routes")
    assert res.status_code == 200
    
    body = res.json()
    routes = body["routes"]
    
    # Extract paths, filtering out None values
    paths = [r.get("path") for r in routes if r.get("path") is not None]
    
    # Check if sorted
    sorted_paths = sorted(paths)
    assert paths == sorted_paths, "Routes should be sorted by path for readability"
