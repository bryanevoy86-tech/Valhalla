"""
PACK CI1: Decision Recommendation Engine Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_generate_decision_recommendations(client):
    """Test generating decision recommendations with context"""
    payload = {
        "source": "heimdall",
        "mode": "growth",
        "context_data": {"net_worth": 5000000, "year": 2024},
        "recommendations": [
            {
                "title": "Acquire commercial property",
                "description": "Prime retail location in downtown",
                "category": "deal",
                "leverage_score": 0.8,
                "risk_score": 0.4,
                "urgency_score": 0.7,
                "alignment_score": 0.9,
            },
            {
                "title": "Hire additional staff",
                "category": "operations",
                "leverage_score": 0.5,
                "risk_score": 0.2,
                "urgency_score": 0.6,
                "alignment_score": 0.8,
            },
        ],
    }
    
    r = client.post("/intelligence/decisions/generate", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["context"]["mode"] == "growth"
    assert len(body["items"]) == 2
    # Items should be sorted by priority_rank
    assert body["items"][0]["priority_rank"] <= body["items"][1]["priority_rank"]


def test_get_decisions_for_context(client):
    """Test retrieving decisions for a specific context"""
    # Create context first
    payload = {
        "source": "manual",
        "mode": "recovery",
        "context_data": {"situation": "cash_flow_crisis"},
        "recommendations": [
            {
                "title": "Cut non-essential expenses",
                "category": "finance",
                "leverage_score": 0.9,
                "risk_score": 0.1,
                "urgency_score": 0.95,
                "alignment_score": 0.7,
            }
        ],
    }
    
    create_r = client.post("/intelligence/decisions/generate", json=payload)
    context_id = create_r.json()["context"]["id"]
    
    # Retrieve decisions for this context
    get_r = client.get(f"/intelligence/decisions/{context_id}")
    assert get_r.status_code == 200
    body = get_r.json()
    assert body["context"]["id"] == context_id
    assert len(body["items"]) == 1
    assert body["items"][0]["title"] == "Cut non-essential expenses"


def test_priority_ranking(client):
    """Test that priority ranking favors high leverage/urgency/alignment, penalizes risk"""
    payload = {
        "source": "auto",
        "mode": "growth",
        "context_data": {},
        "recommendations": [
            {
                "title": "Safe but low-impact",
                "category": "test",
                "leverage_score": 0.1,
                "risk_score": 0.1,
                "urgency_score": 0.1,
                "alignment_score": 0.1,
            },
            {
                "title": "High-impact opportunity",
                "category": "test",
                "leverage_score": 0.9,
                "risk_score": 0.3,
                "urgency_score": 0.8,
                "alignment_score": 0.9,
            },
        ],
    }
    
    r = client.post("/intelligence/decisions/generate", json=payload)
    body = r.json()
    # High-impact should rank better (lower rank value = better)
    assert body["items"][0]["title"] == "High-impact opportunity"
    assert body["items"][1]["title"] == "Safe but low-impact"


def test_context_not_found(client):
    """Test 404 when context doesn't exist"""
    r = client.get("/intelligence/decisions/99999")
    assert r.status_code == 404
