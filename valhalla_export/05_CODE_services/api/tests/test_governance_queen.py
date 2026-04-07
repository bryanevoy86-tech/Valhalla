# services/api/tests/test_governance_queen.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_queen_allows_sane_workload():
    """
    Healthy workload: normal hours, limited projects, low stress.
    Queen should allow.
    """
    payload = {
        "context_type": "plan",
        "data": {
            "hours_per_week": "35",
            "parallel_projects": "2",
            "uses_evenings": "False",
            "uses_weekends": "False",
            "sprint_weeks": "3",
            "stress_level": "5",
            "chaos_factor": "3.0",
        },
    }
    resp = client.post("/api/governance/queen/evaluate", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["allowed"] is True
    assert data["severity"] in ["info", "warn"]


def test_queen_warns_when_hours_are_high_but_not_insane():
    """
    High but not catastrophic hours: Queen should warn, not hard block.
    """
    payload = {
        "context_type": "plan",
        "data": {
            "hours_per_week": "50",  # above preferred 40, below hard cap 55
            "parallel_projects": "3",
            "uses_evenings": "True",
            "uses_weekends": "False",
            "sprint_weeks": "2",
            "stress_level": "7",
            "chaos_factor": "5.0",
        },
    }
    resp = client.post("/api/governance/queen/evaluate", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["allowed"] is True
    assert data["severity"] == "warn"
    assert len(data["reasons"]) >= 1


def test_queen_denies_hard_overload():
    """
    Extreme overload: too many hours + high stress + chaos.
    Queen should deny.
    """
    payload = {
        "context_type": "plan",
        "data": {
            "hours_per_week": "70",   # exceeds hard cap
            "parallel_projects": "6",
            "uses_evenings": "True",
            "uses_weekends": "True",
            "sprint_weeks": "8",
            "stress_level": "10",
            "chaos_factor": "9.0",
        },
    }
    resp = client.post("/api/governance/queen/evaluate", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["allowed"] is False
    assert data["severity"] == "critical"
    assert len(data["reasons"]) >= 1
