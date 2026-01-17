"""
Test suite for metrics, capital intake, and telemetry endpoints.
"""

import os
import httpx
import pytest

API_BASE = os.getenv("API_BASE", "http://localhost:4000")
API_KEY = os.getenv("HEIMDALL_BUILDER_API_KEY", "test123")
TIMEOUT = 10.0


def test_metrics_ok():
    """Test /metrics endpoint returns expected structure"""
    url = f"{API_BASE}/metrics"
    resp = httpx.get(url, timeout=TIMEOUT)
    
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    
    data = resp.json()
    assert data.get("ok") is True
    
    # Check that all expected keys are present
    expected_keys = [
        "research_sources", "research_docs", "telemetry_events",
        "capital_intake_records", "builder_tasks", "playbooks"
    ]
    for key in expected_keys:
        assert key in data, f"Missing key: {key}"
        assert isinstance(data[key], int), f"Key {key} should be int"


def test_capital_roundtrip():
    """Test capital intake create and list endpoints"""
    # Create a capital intake record
    create_url = f"{API_BASE}/capital/intake"
    payload = {
        "source": "test_wholesaling",
        "currency": "CAD",
        "amount": 5000.00,
        "note": "Test intake from pytest"
    }
    headers = {"X-API-Key": API_KEY}
    
    create_resp = httpx.post(create_url, json=payload, headers=headers, timeout=TIMEOUT)
    assert create_resp.status_code == 201, f"Expected 201, got {create_resp.status_code}: {create_resp.text}"
    
    created = create_resp.json()
    assert "id" in created
    assert created["source"] == "test_wholesaling"
    assert created["amount"] == 5000.0
    intake_id = created["id"]
    
    # List capital intake records and verify our record is present
    list_url = f"{API_BASE}/capital/intake"
    list_resp = httpx.get(list_url, headers=headers, timeout=TIMEOUT)
    assert list_resp.status_code == 200, f"Expected 200, got {list_resp.status_code}: {list_resp.text}"
    
    records = list_resp.json()
    assert isinstance(records, list)
    
    # Verify our created record is in the list
    found = any(r["id"] == intake_id for r in records)
    assert found, f"Capital intake ID {intake_id} not found in list"


def test_telemetry_create():
    """Test telemetry event logging"""
    url = f"{API_BASE}/telemetry"
    payload = {
        "kind": "test",
        "message": "Test telemetry event from pytest",
        "meta_json": '{"test": true}'
    }
    headers = {"X-API-Key": API_KEY}
    
    resp = httpx.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    
    data = resp.json()
    assert data.get("ok") is True
    assert "id" in data
    assert data["kind"] == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
