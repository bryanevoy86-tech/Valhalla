"""
PACK AR: Heimdall Workload Balancer Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import get_db
from app.models.base import Base


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_job():
    payload = {
        "job_type": "research",
        "source": "user",
        "priority": "high",
        "payload": {"topic": "market_analysis"},
    }
    res = client.post("/heimdall/workload/jobs", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["job_type"] == "research"
    assert body["status"] == "queued"
    assert body["priority"] == "high"


def test_list_jobs():
    # Create multiple jobs
    for i in range(3):
        client.post(
            "/heimdall/workload/jobs",
            json={
                "job_type": f"job_type_{i}",
                "source": "system",
                "payload": {},
            },
        )

    res = client.get("/heimdall/workload/jobs")
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 3


def test_list_jobs_by_status():
    # Create job
    res = client.post(
        "/heimdall/workload/jobs",
        json={"job_type": "research", "payload": {}},
    )
    job_id = res.json()["id"]

    # Initially queued
    queued_res = client.get("/heimdall/workload/jobs", params={"status": "queued"})
    assert queued_res.status_code == 200
    assert len(queued_res.json()) >= 1

    # Update to in_progress
    client.patch(
        f"/heimdall/workload/jobs/{job_id}",
        json={"status": "in_progress"},
    )

    # Query in_progress
    in_progress_res = client.get(
        "/heimdall/workload/jobs", params={"status": "in_progress"}
    )
    assert in_progress_res.status_code == 200
    assert len(in_progress_res.json()) >= 1


def test_update_job_status():
    # Create job
    res = client.post(
        "/heimdall/workload/jobs",
        json={"job_type": "write_email"},
    )
    job_id = res.json()["id"]

    # Update status
    update_res = client.patch(
        f"/heimdall/workload/jobs/{job_id}",
        json={"status": "completed"},
    )
    assert update_res.status_code == 200
    body = update_res.json()
    assert body["status"] == "completed"
    assert body["completed_at"] is not None


def test_queue_stats():
    # Create jobs with different statuses
    res1 = client.post(
        "/heimdall/workload/jobs",
        json={"job_type": "research"},
    )
    job1_id = res1.json()["id"]

    res2 = client.post(
        "/heimdall/workload/jobs",
        json={"job_type": "analysis"},
    )
    job2_id = res2.json()["id"]

    # Update one to in_progress
    client.patch(
        f"/heimdall/workload/jobs/{job1_id}",
        json={"status": "in_progress"},
    )

    # Update one to completed
    client.patch(
        f"/heimdall/workload/jobs/{job2_id}",
        json={"status": "completed"},
    )

    stats_res = client.get("/heimdall/workload/stats")
    assert stats_res.status_code == 200
    body = stats_res.json()
    assert body["total_jobs"] >= 2
    assert body["queued"] >= 0
    assert body["in_progress"] >= 1
    assert body["completed"] >= 1


def test_set_workload_config():
    res = client.post(
        "/heimdall/workload/config/research",
        params={
            "enabled": True,
            "max_concurrent": 5,
            "notes": "Research job config",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["job_type"] == "research"
    assert body["enabled"] is True
    assert body["max_concurrent"] == 5


def test_get_workload_config():
    # Set config
    client.post(
        "/heimdall/workload/config/analysis",
        params={"enabled": False, "notes": "Disabled"},
    )

    # Get config
    res = client.get("/heimdall/workload/config/analysis")
    assert res.status_code == 200
    body = res.json()
    assert body["job_type"] == "analysis"
    assert body["enabled"] is False


def test_get_nonexistent_config():
    res = client.get("/heimdall/workload/config/nonexistent")
    assert res.status_code == 200
    body = res.json()
    assert body is None


def test_job_lifecycle():
    """Test complete job lifecycle."""
    # Create
    res = client.post(
        "/heimdall/workload/jobs",
        json={
            "job_type": "story",
            "source": "kid_hub",
            "priority": "normal",
            "payload": {"kid_id": "123"},
        },
    )
    job_id = res.json()["id"]
    assert res.json()["status"] == "queued"

    # Start
    res = client.patch(
        f"/heimdall/workload/jobs/{job_id}",
        json={"status": "in_progress"},
    )
    assert res.json()["status"] == "in_progress"
    assert res.json()["started_at"] is not None

    # Complete
    res = client.patch(
        f"/heimdall/workload/jobs/{job_id}",
        json={"status": "completed"},
    )
    assert res.json()["status"] == "completed"
    assert res.json()["completed_at"] is not None


def test_job_priority_levels():
    """Test different priority levels."""
    priorities = ["low", "normal", "high", "critical"]
    for priority in priorities:
        res = client.post(
            "/heimdall/workload/jobs",
            json={"job_type": "test", "priority": priority},
        )
        assert res.status_code == 200
        assert res.json()["priority"] == priority
