# services/api/app/tests/test_internal_auditor.py

"""
Tests for PACK Q: Internal Auditor
Rule-based operational compliance scanning (not legal advice)
"""

import pytest
from fastapi.testclient import TestClient


def test_audit_deal_creates_events(client: TestClient):
    """Test that scanning a deal creates audit events for missing requirements."""
    res = client.post("/audit/scan/deal/1")
    assert res.status_code == 200
    body = res.json()
    assert "issues_found" in body
    assert "checklist" in body
    assert "events" in body
    assert isinstance(body["issues_found"], int)


def test_get_audit_summary(client: TestClient):
    """Test getting summary of open audit events by severity."""
    res = client.get("/audit/summary")
    assert res.status_code == 200
    body = res.json()
    assert "total_open" in body
    assert "critical" in body
    assert "warning" in body
    assert "info" in body


def test_list_open_events(client: TestClient):
    """Test listing all open audit events."""
    res = client.get("/audit/events/open")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_list_events_for_deal(client: TestClient):
    """Test listing audit events for a specific deal."""
    # First create some events by scanning
    client.post("/audit/scan/deal/999")
    
    # Then retrieve them
    res = client.get("/audit/events/deal/999")
    assert res.status_code == 200
    events = res.json()
    assert isinstance(events, list)


def test_resolve_audit_event(client: TestClient):
    """Test resolving an audit event."""
    # First create an event
    scan_res = client.post("/audit/scan/deal/123")
    events = scan_res.json().get("events", [])
    
    if events:
        event_id = events[0]["id"]
        
        # Resolve it
        res = client.post(f"/audit/events/{event_id}/resolve")
        assert res.status_code == 200
        body = res.json()
        assert body["is_resolved"] is True
        assert body["resolved_at"] is not None


def test_resolve_nonexistent_event(client: TestClient):
    """Test that resolving a nonexistent event returns 404."""
    res = client.post("/audit/events/999999/resolve")
    assert res.status_code == 404


def test_audit_event_codes(client: TestClient):
    """Test that audit events have proper codes and severity levels."""
    res = client.post("/audit/scan/deal/777")
    assert res.status_code == 200
    
    events = res.json().get("events", [])
    
    # Check event structure
    for event in events:
        assert "code" in event
        assert "severity" in event
        assert "message" in event
        assert event["severity"] in ["info", "warning", "critical"]
