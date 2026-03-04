"""
Tests for PACK CL18: EIA Report Generator
"""

from fastapi.testclient import TestClient


def test_generate_eia_monthly_report(client: TestClient):
    r = client.post(
        "/eia/monthly-report",
        json={"period": "2026-03", "title": "March 2026 EIA Monthly Report", "notes": "Auto-generated snapshot"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["evidence_type"] == "EIA_MONTHLY_REPORT"
