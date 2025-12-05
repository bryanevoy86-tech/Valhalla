# services/api/tests/test_governance_loki.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_loki_allows_modest_downside():
    """
    Healthy risk profile: modest downside, low ruin probability,
    moderate correlation, acceptable hidden complexity.
    Loki should allow.
    """
    payload = {
        "context_type": "deal_risk",
        "data": {
            "capital_at_risk": "100000",
            "worst_case_loss": "80000",  # 0.8x
            "probability_of_ruin": "0.02",
            "correlation_with_portfolio": "0.5",
            "hidden_complexity_score": "4",
        },
    }
    resp = client.post("/api/governance/loki/evaluate", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["allowed"] is True
    assert data["severity"] in ["info", "warn"]


def test_loki_warns_but_allows_borderline_risk():
    """
    Borderline scenario: close to limits but not clearly suicidal.
    Loki may warn but still allow.
    """
    payload = {
        "context_type": "deal_risk",
        "data": {
            "capital_at_risk": "100000",
            "worst_case_loss": "140000",  # 1.4x, below 1.5x limit
            "probability_of_ruin": "0.04",  # below 5%
            "correlation_with_portfolio": "0.78",
            "hidden_complexity_score": "7",  # at edge
        },
    }
    resp = client.post("/api/governance/loki/evaluate", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["allowed"] is True
    assert data["severity"] in ["info", "warn"]


def test_loki_denies_extreme_downside_or_ruin():
    """
    Extreme risk scenario: very high downside, ruin probability,
    correlation or hidden complexity. Loki should deny.
    """
    payload = {
        "context_type": "deal_risk",
        "data": {
            "capital_at_risk": "50000",
            "worst_case_loss": "100000",  # 2x
            "probability_of_ruin": "0.15",
            "correlation_with_portfolio": "0.9",
            "hidden_complexity_score": "9",
        },
    }
    resp = client.post("/api/governance/loki/evaluate", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["allowed"] is False
    assert data["severity"] == "critical"
    assert len(data["reasons"]) >= 1
