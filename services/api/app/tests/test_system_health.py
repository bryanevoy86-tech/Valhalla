"""
PACK TX: System Health Tests
Tests for liveness, readiness, and metrics probes.
"""

import pytest


def test_liveness_probe(client):
    """Test Kubernetes liveness probe endpoint."""
    res = client.get("/system-health/live")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "timestamp" in body
    assert "message" in body


def test_readiness_probe(client):
    """Test Kubernetes readiness probe endpoint."""
    res = client.get("/system-health/ready")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] in ["ready", "maintenance"]
    assert "db_ok" in body
    assert "timestamp" in body
    assert "message" in body


def test_metrics_endpoint(client):
    """Test metrics endpoint returns uptime info."""
    res = client.get("/system-health/metrics")
    assert res.status_code == 200
    body = res.json()
    assert "timestamp" in body
    assert "uptime_seconds" in body
    assert body["uptime_seconds"] >= 0


def test_health_endpoint_still_works(client):
    """Test that original health endpoint still works."""
    res = client.get("/system-health")
    assert res.status_code == 200
    body = res.json()
    assert "timestamp" in body
