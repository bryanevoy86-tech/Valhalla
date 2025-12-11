"""
PACK CI3: Trajectory Engine Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_create_trajectory_target(client):
    """Test creating a trajectory target"""
    payload = {
        "name": "5-year net worth goal",
        "category": "finance",
        "description": "Reach $10 million net worth",
        "target_value": 10000000,
        "unit": "CAD",
        "horizon_days": 1825,
    }
    
    r = client.post("/intelligence/trajectory/targets", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "5-year net worth goal"
    assert body["target_value"] == 10000000


def test_record_on_track_snapshot(client):
    """Test recording a snapshot that's on track"""
    # Create target first
    target_r = client.post(
        "/intelligence/trajectory/targets",
        json={
            "name": "Monthly revenue target",
            "category": "finance",
            "target_value": 100000,
            "unit": "CAD",
            "horizon_days": 30,
        },
    )
    target_id = target_r.json()["id"]
    
    # Record snapshot close to target
    snapshot_r = client.post(
        "/intelligence/trajectory/snapshots",
        json={
            "target_id": target_id,
            "current_value": 102000,  # slightly above
            "expected_value": 100000,
        },
    )
    assert snapshot_r.status_code == 200
    body = snapshot_r.json()
    assert body["status"] == "on_track"
    assert body["deviation"] == 2000


def test_record_behind_snapshot(client):
    """Test recording a snapshot that's behind"""
    target_r = client.post(
        "/intelligence/trajectory/targets",
        json={
            "name": "Deal closures",
            "category": "operations",
            "target_value": 4,
            "unit": "deals/month",
            "horizon_days": 30,
        },
    )
    target_id = target_r.json()["id"]
    
    # Record behind snapshot
    snapshot_r = client.post(
        "/intelligence/trajectory/snapshots",
        json={
            "target_id": target_id,
            "current_value": 2,
            "expected_value": 4,
        },
    )
    assert snapshot_r.status_code == 200
    body = snapshot_r.json()
    assert body["status"] == "behind"
    assert body["deviation"] == -2


def test_record_ahead_snapshot(client):
    """Test recording a snapshot that's ahead"""
    target_r = client.post(
        "/intelligence/trajectory/targets",
        json={
            "name": "System reliability",
            "category": "system",
            "target_value": 99.5,
            "unit": "%",
            "horizon_days": 365,
        },
    )
    target_id = target_r.json()["id"]
    
    # Record ahead snapshot
    snapshot_r = client.post(
        "/intelligence/trajectory/snapshots",
        json={
            "target_id": target_id,
            "current_value": 99.95,
            "expected_value": 99.5,
        },
    )
    assert snapshot_r.status_code == 200
    body = snapshot_r.json()
    assert body["status"] == "ahead"
    assert body["deviation"] > 0


def test_list_snapshots_for_target(client):
    """Test listing snapshots for a target"""
    target_r = client.post(
        "/intelligence/trajectory/targets",
        json={
            "name": "Test target",
            "category": "finance",
            "target_value": 1000,
            "unit": "units",
            "horizon_days": 365,
        },
    )
    target_id = target_r.json()["id"]
    
    # Record multiple snapshots
    for i in range(3):
        client.post(
            "/intelligence/trajectory/snapshots",
            json={
                "target_id": target_id,
                "current_value": 1000 + (i * 100),
                "expected_value": 1000 + (i * 100),
            },
        )
    
    # List snapshots
    r = client.get(f"/intelligence/trajectory/targets/{target_id}/snapshots")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    # Should be sorted by taken_at desc
    assert body["items"][0]["current_value"] > body["items"][-1]["current_value"]


def test_snapshot_with_details(client):
    """Test recording snapshot with detailed context"""
    target_r = client.post(
        "/intelligence/trajectory/targets",
        json={
            "name": "Health score",
            "category": "health",
            "target_value": 85,
            "unit": "points",
            "horizon_days": 180,
        },
    )
    target_id = target_r.json()["id"]
    
    snapshot_r = client.post(
        "/intelligence/trajectory/snapshots",
        json={
            "target_id": target_id,
            "current_value": 82,
            "expected_value": 85,
            "details": {
                "sleep_quality": 7,
                "exercise_frequency": 4,
                "stress_level": 6,
            },
        },
    )
    assert snapshot_r.status_code == 200
    body = snapshot_r.json()
    assert body["details"]["sleep_quality"] == 7
