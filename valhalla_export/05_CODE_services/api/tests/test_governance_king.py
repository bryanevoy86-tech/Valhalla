# services/api/tests/test_governance_king.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_king_allows_safe_deal():
    payload = {
        "context_type": "deal",
        "data": {
            "purchase_price": "200000",
            "repairs": "20000",
            "arv": "300000",
            "roi": "0.20"
        }
    }
    resp = client.post("/api/governance/king/evaluate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["allowed"] is True
    assert data["severity"] in ["info", "warn"]


def test_king_denies_predatory_deal():
    payload = {
        "context_type": "deal",
        "data": {
            "purchase_price": "200000",
            "repairs": "20000",
            "arv": "300000",
            "predatory": "True"
        }
    }
    resp = client.post("/api/governance/king/evaluate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["allowed"] is False
    assert data["severity"] == "critical"


def test_king_warns_low_roi():
    payload = {
        "context_type": "deal",
        "data": {
            "purchase_price": "200000",
            "repairs": "20000",
            "arv": "215000",
            "roi": "0.03"   # Low ROI — King should warn
        }
    }
    resp = client.post("/api/governance/king/evaluate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["allowed"] is True   # low ROI is warn, not denial
    assert data["severity"] == "warn"
