"""
Tests for PACK CL19: Exports
"""

from fastapi.testclient import TestClient


def test_export_compliance_evidence(client: TestClient):
    # Should always return 200 even if empty
    r = client.get("/exports/compliance/evidence")
    assert r.status_code == 200
    assert "total" in r.json()
