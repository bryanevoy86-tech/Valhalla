"""
PACK TO: Daily Rhythm & Tempo Tests
"""

import pytest
from fastapi.testclient import TestClient


def test_create_rhythm_profile(client: TestClient):
    """Test creating a daily rhythm profile."""
    response = client.post(
        "/rhythm/profiles",
        json={
            "name": "default",
            "wake_time": "07:00",
            "sleep_time": "23:00",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "default"
    assert data["wake_time"] == "07:00"
    assert data["sleep_time"] == "23:00"
    assert data["active"] is True
    assert "id" in data


def test_list_rhythm_profiles(client: TestClient):
    """Test listing daily rhythm profiles."""
    # Create a profile
    client.post(
        "/rhythm/profiles",
        json={"name": "weekend", "wake_time": "08:00"},
    )

    # List profiles
    response = client.get("/rhythm/profiles")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_create_tempo_rule(client: TestClient):
    """Test creating a tempo rule."""
    response = client.post(
        "/rhythm/tempo-rules",
        json={
            "profile_name": "default",
            "time_block": "morning",
            "action_intensity": "push",
            "communication_style": "detailed",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["profile_name"] == "default"
    assert data["time_block"] == "morning"
    assert data["action_intensity"] == "push"
    assert data["communication_style"] == "detailed"
    assert "id" in data


def test_list_tempo_rules(client: TestClient):
    """Test listing tempo rules."""
    # Create a rule
    client.post(
        "/rhythm/tempo-rules",
        json={
            "profile_name": "default",
            "time_block": "afternoon",
            "action_intensity": "balanced",
            "communication_style": "short",
        },
    )

    # List rules
    response = client.get("/rhythm/tempo-rules")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_list_tempo_rules_by_profile(client: TestClient):
    """Test listing tempo rules for a specific profile."""
    # Create rules for different profiles
    client.post(
        "/rhythm/tempo-rules",
        json={
            "profile_name": "weekday",
            "time_block": "morning",
            "action_intensity": "push",
            "communication_style": "detailed",
        },
    )

    # List rules for specific profile
    response = client.get("/rhythm/tempo-rules?profile_name=weekday")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert data[0]["profile_name"] == "weekday"


def test_daily_rhythm_snapshot(client: TestClient):
    """Test getting daily rhythm snapshot."""
    # Create profile
    client.post(
        "/rhythm/profiles",
        json={
            "name": "default",
            "wake_time": "07:00",
            "sleep_time": "23:00",
            "active": True,
        },
    )

    # Create tempo rule
    client.post(
        "/rhythm/tempo-rules",
        json={
            "profile_name": "default",
            "time_block": "morning",
            "action_intensity": "push",
            "communication_style": "detailed",
        },
    )

    # Get snapshot
    response = client.get("/rhythm/snapshot")
    assert response.status_code == 200
    data = response.json()
    assert "profile" in data
    assert "rules" in data
    assert "meta" in data
    assert data["profile"]["name"] == "default"


def test_daily_rhythm_snapshot_not_found(client: TestClient):
    """Test getting snapshot for non-existent profile."""
    response = client.get("/rhythm/snapshot?profile_name=nonexistent")
    assert response.status_code == 404
