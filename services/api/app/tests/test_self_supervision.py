"""
Tests for PACK CL13: Self-Supervision
"""

from fastapi.testclient import TestClient


def test_create_supervision_run(client: TestClient):
    resp = client.post(
        "/heimdall/supervision/runs",
        json={
            "run_id": "run-001",
            "trigger": "manual",
            "scope": "decisions",
            "summary": "Quick audit pass",
            "metrics": {"checked": 12, "drift": 0.08},
            "findings": [
                {
                    "finding_type": "logic_drift",
                    "severity": "medium",
                    "title": "Minor drift in lead scoring",
                    "detail": "Scoring weights changed without review",
                    "context": {"module": "leads", "field": "score"},
                }
            ],
        },
    )
    assert resp.status_code == 201, resp.text

    runs = client.get("/heimdall/supervision/runs")
    assert runs.status_code == 200
    assert runs.json()["total"] >= 1

    findings = client.get("/heimdall/supervision/findings?unresolved_only=true")
    assert findings.status_code == 200
    assert findings.json()["total"] >= 1
