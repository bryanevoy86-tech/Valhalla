"""
PACK TN: Trust & Relationship Mapping Tests
"""

import pytest
from fastapi.testclient import TestClient


def test_create_relationship_profile(client: TestClient):
    """Test creating a relationship profile."""
    response = client.post(
        "/relationships/profiles",
        json={
            "name": "Accountant Bob",
            "role": "professional",
            "user_trust_level": 7.5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Accountant Bob"
    assert data["role"] == "professional"
    assert data["user_trust_level"] == 7.5
    assert "id" in data


def test_list_relationship_profiles(client: TestClient):
    """Test listing relationship profiles."""
    # Create a profile
    client.post(
        "/relationships/profiles",
        json={"name": "Family Member", "role": "family"},
    )

    # List profiles
    response = client.get("/relationships/profiles")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_create_trust_event(client: TestClient):
    """Test creating a trust event."""
    # Create profile first
    profile_response = client.post(
        "/relationships/profiles",
        json={
            "name": "Contractor Sarah",
            "role": "professional",
            "user_trust_level": 6.0,
        },
    )
    profile_id = profile_response.json()["id"]

    # Create trust event
    response = client.post(
        "/relationships/events",
        json={
            "profile_id": profile_id,
            "event_description": "Delivered reports on time",
            "trust_change": 0.5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["profile_id"] == profile_id
    assert data["event_description"] == "Delivered reports on time"
    assert data["trust_change"] == 0.5
    assert "id" in data
    assert "date" in data


def test_create_trust_event_invalid_profile(client: TestClient):
    """Test creating a trust event with non-existent profile."""
    response = client.post(
        "/relationships/events",
        json={
            "profile_id": 99999,
            "event_description": "Some event",
        },
    )
    assert response.status_code == 404


def test_list_trust_events(client: TestClient):
    """Test listing trust events."""
    # Create profile
    profile_response = client.post(
        "/relationships/profiles",
        json={"name": "Test Person", "role": "friend"},
    )
    profile_id = profile_response.json()["id"]

    # Create event
    client.post(
        "/relationships/events",
        json={
            "profile_id": profile_id,
            "event_description": "Had helpful conversation",
        },
    )

    # List events
    response = client.get("/relationships/events")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_relationship_snapshot(client: TestClient):
    """Test getting relationship snapshot."""
    # Create profile
    profile_response = client.post(
        "/relationships/profiles",
        json={"name": "Snapshot Test", "role": "colleague"},
    )
    profile_id = profile_response.json()["id"]

    # Create event
    client.post(
        "/relationships/events",
        json={
            "profile_id": profile_id,
            "event_description": "Positive interaction",
        },
    )

    # Get snapshot
    response = client.get("/relationships/snapshot")
    assert response.status_code == 200
    data = response.json()
    assert "profiles" in data
    assert "trust_events" in data
    assert len(data["profiles"]) > 0
