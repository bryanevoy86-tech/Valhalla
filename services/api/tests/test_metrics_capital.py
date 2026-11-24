"""
Test suite for metrics, capital intake, and telemetry endpoints.
"""

import pytest



def test_metrics_ok(legacy_http_client):
    client, _ = legacy_http_client
    """Test /metrics endpoint returns expected structure"""
    url = "/metrics"
    resp = client.get(url)
    
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


def test_capital_roundtrip(legacy_http_client):
    client, _ = legacy_http_client
    """Test capital intake create and list endpoints"""
    # Create a capital intake record
    create_url = "/capital/intake"
    payload = {
        "source": "test_wholesaling",
        "currency": "CAD",
        "amount": 5000.00,
        "note": "Test intake from pytest"
    }
    
    create_resp = client.post(create_url, json=payload)
    assert create_resp.status_code == 201, f"Expected 201, got {create_resp.status_code}: {create_resp.text}"
    
    created = create_resp.json()
    assert "id" in created
    assert created["source"] == "test_wholesaling"
    assert created["amount"] == 5000.0
    intake_id = created["id"]
    
    # List capital intake records and verify our record is present
    list_url = "/capital/intake"
    list_resp = client.get(list_url)
    assert list_resp.status_code == 200, f"Expected 200, got {list_resp.status_code}: {list_resp.text}"
    
    records = list_resp.json()
    assert isinstance(records, list)
    
    # Verify our created record is in the list
    found = any(r["id"] == intake_id for r in records)
    assert found, f"Capital intake ID {intake_id} not found in list"


def test_telemetry_create(legacy_http_client):
    client, engine = legacy_http_client
    from sqlalchemy.orm import Session
    from app.models.telemetry import IntegrityEvent

    response = client.post("/telemetry/", json={
        "event": "test", "actor": "pytest", "meta": {"test": True},
    })
    assert response.status_code == 201, response.text
    event = response.json()
    assert event["event"] == "test"
    assert event["meta"] == {"test": True}
    with Session(engine) as db:
        assert db.get(IntegrityEvent, event["id"]).source == "pytest"
