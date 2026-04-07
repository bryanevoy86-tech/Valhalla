"""
PACK TU: Error Handling Tests
Tests for global error handlers and ProblemDetails responses.
"""

import pytest
from fastapi.testclient import TestClient


def test_validation_error_has_problem_details(client):
    """Test that validation errors return ProblemDetails format with correlation_id."""
    # Call an endpoint with bad validation (bad date format)
    res = client.get("/timeline/snapshot", params={"from_date": "not-a-date", "to_date": "also-bad"})
    assert res.status_code == 422
    body = res.json()
    
    assert "title" in body
    assert body["title"] == "Validation error"
    assert "status" in body
    assert body["status"] == 422
    assert "correlation_id" in body
    assert body["correlation_id"] is not None


def test_http_exception_has_correlation_id(client):
    """Test that HTTP exceptions include correlation_id."""
    res = client.get("/nonexistent-endpoint")
    assert res.status_code == 404
    body = res.json()
    
    assert "correlation_id" in body
    assert body["correlation_id"] is not None


def test_error_has_instance_field(client):
    """Test that error responses include instance field with the request URL."""
    res = client.get("/nonexistent")
    assert res.status_code == 404
    body = res.json()
    
    assert "instance" in body
    assert body["instance"] is not None
