"""
Tests for PACK CL20: System Readiness
"""

from fastapi.testclient import TestClient


def test_readiness_endpoint(client: TestClient):
    r = client.get("/system/readiness/")
    assert r.status_code == 200
    assert "ready" in r.json()
    assert "checklist_score" in r.json()
