"""
PACK UH: Export Job Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_create_export_job(client):
    """Test create export job"""
    s = client.post(
        "/system/exports/",
        json={
            "job_type": "audit_log_export",
            "requested_by": "admin@example.com",
        },
    )
    assert s.status_code == 200
    assert s.json()["status"] == "pending"
    assert s.json()["job_type"] == "audit_log_export"


def test_create_export_with_filter_params(client):
    """Test create export job with filter parameters"""
    s = client.post(
        "/system/exports/",
        json={
            "job_type": "audit_log_export",
            "filter_params": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            "requested_by": "admin@example.com",
        },
    )
    assert s.status_code == 200
    assert s.json()["job_type"] == "audit_log_export"


def test_list_export_jobs(client):
    """Test list export jobs"""
    r = client.get("/system/exports/")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body
    assert "items" in body


def test_list_exports_by_status(client):
    """Test list exports filtered by status"""
    # Create a job first
    job = client.post(
        "/system/exports/",
        json={
            "job_type": "snapshot_export",
            "requested_by": "user@example.com",
        },
    ).json()
    
    # List by status
    r = client.get(f"/system/exports/?status=pending")
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 1


def test_update_export_job_status(client):
    """Test update export job status"""
    # Create job
    job = client.post(
        "/system/exports/",
        json={
            "job_type": "full_export",
            "requested_by": "admin@example.com",
        },
    ).json()
    
    # Update status
    u = client.post(
        f"/system/exports/{job['id']}/status",
        json={
            "status": "completed",
            "storage_url": "s3://bucket/exports/job-123.csv",
        },
    )
    assert u.status_code == 200
    assert u.json()["status"] == "completed"
