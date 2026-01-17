"""
PACK CI8: Narrative / Chapter Engine Test Suite
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_create_narrative_chapter(client):
    """Test creating a narrative chapter."""
    response = client.post("/intelligence/narrative/chapters", json={
        "name": "Chapter 1: Foundation",
        "slug": "ch1_foundation",
        "description": "Building the empire foundation",
        "phase_order": 1,
        "goals": {
            "financial_stability": 100000,
            "team_size": 5,
        },
        "exit_conditions": {
            "min_cash_flow": 50000,
            "min_team_maturity": 3,
        },
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Chapter 1: Foundation"
    assert data["slug"] == "ch1_foundation"


def test_upsert_narrative_chapter(client):
    """Test updating a narrative chapter by slug (idempotent)."""
    client.post("/intelligence/narrative/chapters", json={
        "name": "Growth Phase",
        "slug": "growth_phase",
        "phase_order": 2,
    })
    
    response = client.post("/intelligence/narrative/chapters", json={
        "name": "Growth Phase Updated",
        "slug": "growth_phase",
        "phase_order": 2,
        "description": "Updated description",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Growth Phase Updated"


def test_list_narrative_chapters(client):
    """Test listing narrative chapters sorted by phase_order."""
    for i in range(3):
        client.post("/intelligence/narrative/chapters", json={
            "name": f"Chapter {i}",
            "slug": f"ch_{i}",
            "phase_order": i + 1,
        })
    
    response = client.get("/intelligence/narrative/chapters")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_chapter_with_exit_conditions(client):
    """Test chapter with complex exit conditions."""
    response = client.post("/intelligence/narrative/chapters", json={
        "name": "War Room",
        "slug": "war_room",
        "phase_order": 5,
        "exit_conditions": {
            "revenue_target": 1000000,
            "team_retention": 0.95,
            "systems_automated": ["payroll", "reporting", "marketing"],
            "cash_position": {
                "min": 100000,
                "target": 500000,
            },
        },
    })
    assert response.status_code == 200
    data = response.json()
    assert "exit_conditions" in data


def test_add_narrative_event(client):
    """Test adding an event to a chapter."""
    ch_resp = client.post("/intelligence/narrative/chapters", json={
        "name": "Event Test",
        "slug": "event_test",
        "phase_order": 1,
    })
    chapter_id = ch_resp.json()["id"]
    
    response = client.post("/intelligence/narrative/events", json={
        "chapter_id": chapter_id,
        "title": "First Hire",
        "description": "Hired first team member",
        "tags": {"milestone": "hiring", "impact": "high"},
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "First Hire"


def test_list_events_for_chapter(client):
    """Test listing events for a chapter."""
    ch_resp = client.post("/intelligence/narrative/chapters", json={
        "name": "Event List",
        "slug": "event_list",
        "phase_order": 1,
    })
    chapter_id = ch_resp.json()["id"]
    
    for i in range(3):
        client.post("/intelligence/narrative/events", json={
            "chapter_id": chapter_id,
            "title": f"Event {i}",
            "description": f"Event {i} description",
        })
    
    response = client.get(f"/intelligence/narrative/chapters/{chapter_id}/events")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_event_with_custom_occurred_at(client):
    """Test creating event with custom timestamp."""
    ch_resp = client.post("/intelligence/narrative/chapters", json={
        "name": "Custom Time",
        "slug": "custom_time",
        "phase_order": 1,
    })
    chapter_id = ch_resp.json()["id"]
    
    response = client.post("/intelligence/narrative/events", json={
        "chapter_id": chapter_id,
        "title": "Historical Event",
        "description": "Event with custom timestamp",
        "occurred_at": "2023-06-15T14:30:00Z",
    })
    assert response.status_code == 200
    data = response.json()
    assert "occurred_at" in data


def test_event_limit_parameter(client):
    """Test limiting events with query parameter."""
    ch_resp = client.post("/intelligence/narrative/chapters", json={
        "name": "Limit Test",
        "slug": "limit_test",
        "phase_order": 1,
    })
    chapter_id = ch_resp.json()["id"]
    
    for i in range(10):
        client.post("/intelligence/narrative/events", json={
            "chapter_id": chapter_id,
            "title": f"Event {i}",
        })
    
    response = client.get(f"/intelligence/narrative/chapters/{chapter_id}/events?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 5


def test_set_active_chapter(client):
    """Test setting the active chapter."""
    ch_resp = client.post("/intelligence/narrative/chapters", json={
        "name": "Active Chapter",
        "slug": "active_ch",
        "phase_order": 1,
    })
    chapter_id = ch_resp.json()["id"]
    
    response = client.post("/intelligence/narrative/active", json={
        "chapter_id": chapter_id,
        "reason": "Moving into growth phase",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["chapter_id"] == chapter_id


def test_get_active_chapter(client):
    """Test retrieving the active chapter."""
    ch_resp = client.post("/intelligence/narrative/chapters", json={
        "name": "Get Active",
        "slug": "get_active",
        "phase_order": 1,
    })
    chapter_id = ch_resp.json()["id"]
    
    client.post("/intelligence/narrative/active", json={
        "chapter_id": chapter_id,
        "reason": "Test",
    })
    
    response = client.get("/intelligence/narrative/active")
    assert response.status_code == 200
    data = response.json()
    assert "chapter_id" in data
    assert "changed_at" in data


def test_switch_chapters(client):
    """Test switching between chapters."""
    ch1_resp = client.post("/intelligence/narrative/chapters", json={
        "name": "Chapter 1",
        "slug": "ch1",
        "phase_order": 1,
    })
    ch1_id = ch1_resp.json()["id"]
    
    ch2_resp = client.post("/intelligence/narrative/chapters", json={
        "name": "Chapter 2",
        "slug": "ch2",
        "phase_order": 2,
    })
    ch2_id = ch2_resp.json()["id"]
    
    client.post("/intelligence/narrative/active", json={
        "chapter_id": ch1_id,
        "reason": "Start",
    })
    
    response = client.post("/intelligence/narrative/active", json={
        "chapter_id": ch2_id,
        "reason": "Progress",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["chapter_id"] == ch2_id


def test_active_chapter_timestamps(client):
    """Test that active chapter tracks change timestamps."""
    ch_resp = client.post("/intelligence/narrative/chapters", json={
        "name": "Timestamp Test",
        "slug": "ts_test",
        "phase_order": 1,
    })
    chapter_id = ch_resp.json()["id"]
    
    resp = client.post("/intelligence/narrative/active", json={
        "chapter_id": chapter_id,
        "reason": "First",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "changed_at" in data
