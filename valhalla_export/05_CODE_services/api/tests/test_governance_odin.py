# services/api/tests/test_governance_odin.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_odin_allows_strong_vertical():
    """
    Healthy new vertical: good profit, reasonable complexity, few verticals.
    Odin should allow.
    """
    payload = {
        "context_type": "new_vertical",
        "data": {
            "active_verticals": "2",
            "new_verticals": "1",
            "estimated_annual_profit": "250000",
            "complexity_score": "5",
            "time_to_break_even_months": "12",
            "mission_critical": "True",
            "distraction_score": "2",
        },
    }
    resp = client.post("/api/governance/odin/evaluate", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["allowed"] is True
    assert data["severity"] in ["info", "warn"]


def test_odin_warns_marginal_project():
    """
    Borderline project: profit OK but complexity high or break-even long.
    Odin should usually warn, not hard block.
    """
    payload = {
        "context_type": "project",
        "data": {
            "active_verticals": "3",
            "new_verticals": "0",
            "estimated_annual_profit": "120000",
            "complexity_score": "7",  # at the edge
            "time_to_break_even_months": "18",  # at the edge
            "mission_critical": "True",
            "distraction_score": "3",
        },
    }
    resp = client.post("/api/governance/odin/evaluate", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["allowed"] is True
    assert data["severity"] in ["info", "warn"]


def test_odin_denies_distraction_or_overload():
    """
    Too many verticals, low profit, high complexity, or clearly a distraction.
    Odin should deny.
    """
    payload = {
        "context_type": "new_vertical",
        "data": {
            "active_verticals": "5",
            "new_verticals": "2",  # will exceed limit
            "estimated_annual_profit": "50000",  # below minimum
            "complexity_score": "9",
            "time_to_break_even_months": "30",
            "mission_critical": "False",
            "distraction_score": "9",
        },
    }
    resp = client.post("/api/governance/odin/evaluate", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["allowed"] is False
    assert data["severity"] == "critical"
    assert len(data["reasons"]) >= 1
