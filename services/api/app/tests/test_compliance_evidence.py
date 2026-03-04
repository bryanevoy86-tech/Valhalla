"""
Tests for PACK CL16: Compliance Evidence Vault
"""

from fastapi.testclient import TestClient


def test_create_and_list_evidence(client: TestClient):
    resp = client.post(
        "/compliance/evidence/",
        json={
            "evidence_id": "ev-001",
            "evidence_type": "EIA_MONTHLY_REPORT",
            "period": "2026-03",
            "title": "March 2026 EIA Monthly Report",
            "notes": "Generated from QB export + activity logs",
            "references": {"qb_report": "profit_loss_2026_03", "files": ["reports/march.pdf"]},
        },
    )
    assert resp.status_code == 201, resp.text

    lst = client.get("/compliance/evidence/?evidence_type=EIA_MONTHLY_REPORT")
    assert lst.status_code == 200
    assert lst.json()["total"] >= 1
