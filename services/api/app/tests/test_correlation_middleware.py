"""
PACK TW: Correlation ID Middleware Tests
Tests for request correlation ID tracking.
"""

import pytest


def test_correlation_id_header_present(client):
    """Test that response includes X-Request-ID header."""
    res = client.get("/system-health")
    assert res.status_code == 200
    assert "X-Request-ID" in res.headers
    assert res.headers["X-Request-ID"]
    assert len(res.headers["X-Request-ID"]) > 0


def test_correlation_id_persists_across_responses(client):
    """Test that passing X-Request-ID header preserves it in response."""
    incoming_id = "test-correlation-123"
    headers = {"X-Request-ID": incoming_id}
    res = client.get("/system-health", headers=headers)
    
    assert res.status_code == 200
    assert res.headers["X-Request-ID"] == incoming_id


def test_correlation_id_is_uuid_when_not_provided(client):
    """Test that generated correlation IDs are valid UUIDs."""
    res = client.get("/system-health")
    assert res.status_code == 200
    
    correlation_id = res.headers["X-Request-ID"]
    # Should be a valid UUID format (36 chars with hyphens)
    assert len(correlation_id) == 36
    assert correlation_id.count("-") == 4
