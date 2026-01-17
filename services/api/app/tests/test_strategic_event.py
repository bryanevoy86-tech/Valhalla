"""
Tests for PACK CL11: Strategic Memory Timeline
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_create_strategic_event(client: TestClient):
    """Test recording a strategic event."""
    response = client.post(
        "/heimdall/timeline/",
        json={
            "event_type": "mode_change",
            "title": "Switched to growth mode",
            "description": "Market opportunity detected, transitioning from maintenance to expansion strategy",
            "domain": "business",
            "context": {
                "from_mode": "recovery",
                "to_mode": "growth",
                "reason_code": "market_opportunity",
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "mode_change"
    assert data["title"] == "Switched to growth mode"


def test_create_event_with_ref_id(client: TestClient):
    """Test creating an event with a reference ID."""
    response = client.post(
        "/heimdall/timeline/",
        json={
            "event_type": "deal",
            "ref_id": "prop_12345",
            "title": "Acquisition closed",
            "description": "Successfully closed on multi-unit commercial property",
            "domain": "business",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["ref_id"] == "prop_12345"


def test_get_events_empty(client: TestClient):
    """Test getting events when none exist."""
    response = client.get("/heimdall/timeline/")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_list_strategic_events(client: TestClient):
    """Test listing strategic events."""
    # Create multiple events
    client.post(
        "/heimdall/timeline/",
        json={
            "event_type": "crisis",
            "title": "Market downturn detected",
            "domain": "market",
            "context": {"market_drop_pct": 15},
        },
    )
    client.post(
        "/heimdall/timeline/",
        json={
            "event_type": "win",
            "title": "Portfolio milestone reached",
            "domain": "business",
            "context": {"new_net_worth": 5000000},
        },
    )

    response = client.get("/heimdall/timeline/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2


def test_filter_events_by_domain(client: TestClient):
    """Test filtering events by domain."""
    response = client.get("/heimdall/timeline/?domain=business")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["domain"] == "business"


def test_filter_events_by_type(client: TestClient):
    """Test filtering events by event_type."""
    response = client.get("/heimdall/timeline/?event_type=mode_change")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["event_type"] == "mode_change"


def test_event_ordering_descending(client: TestClient):
    """Test that events are returned in descending chronological order."""
    response = client.get("/heimdall/timeline/?limit=100")
    assert response.status_code == 200
    data = response.json()
    
    # Check ordering (most recent first)
    items = data["items"]
    for i in range(len(items) - 1):
        assert items[i]["occurred_at"] >= items[i + 1]["occurred_at"]


def test_event_with_all_fields(client: TestClient):
    """Test creating event with all optional fields."""
    from datetime import datetime, timedelta

    occurred = datetime.utcnow() - timedelta(days=30)
    response = client.post(
        "/heimdall/timeline/",
        json={
            "event_type": "rule_change",
            "ref_id": "rule_constraint_5",
            "title": "Updated custody constraint policy",
            "description": "Modified schedule constraints based on new living arrangement",
            "domain": "personal",
            "context": {
                "old_constraint": "fixed schedule",
                "new_constraint": "flexible with 48hr notice",
                "effective_date": "2025-01-15",
            },
            "occurred_at": occurred.isoformat(),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "rule_change"
    assert data["ref_id"] == "rule_constraint_5"


def test_limit_parameter(client: TestClient):
    """Test the limit parameter for pagination."""
    response = client.get("/heimdall/timeline/?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 5
