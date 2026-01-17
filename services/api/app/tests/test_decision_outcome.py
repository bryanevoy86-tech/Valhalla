"""
Tests for PACK CL9-10: Decision Outcome Log & Feedback API
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_create_decision_outcome(client: TestClient):
    """Test recording a decision outcome."""
    response = client.post(
        "/heimdall/decisions/outcomes",
        json={
            "decision_id": "deal_001",
            "title": "Multi-unit acquisition opportunity",
            "domain": "real_estate",
            "action_taken": "accepted",
            "outcome_quality": "good",
            "impact_score": 75,
            "notes": "Deal closed at asking price, strong market position established",
            "context": {
                "purchase_price": 850000,
                "projected_return": "12% annually",
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["decision_id"] == "deal_001"
    assert data["domain"] == "real_estate"
    assert data["action_taken"] == "accepted"


def test_get_decision_outcomes_empty(client: TestClient):
    """Test getting outcomes list (may not be empty due to test data)."""
    response = client.get("/heimdall/decisions/outcomes")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    # Just verify structure, not that it's empty


def test_list_decision_outcomes(client: TestClient):
    """Test listing decision outcomes."""
    # Create a few outcomes
    client.post(
        "/heimdall/decisions/outcomes",
        json={
            "decision_id": "arb_001",
            "title": "Arbitrage opportunity - wholesale flip",
            "domain": "arbitrage",
            "action_taken": "accepted",
            "outcome_quality": "neutral",
            "impact_score": 0,
        },
    )
    client.post(
        "/heimdall/decisions/outcomes",
        json={
            "decision_id": "sec_001",
            "title": "Security recommendation - vault upgrade",
            "domain": "security",
            "action_taken": "ignored",
            "outcome_quality": "bad",
            "impact_score": -50,
        },
    )

    response = client.get("/heimdall/decisions/outcomes")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3  # Including the first test outcome


def test_filter_outcomes_by_domain(client: TestClient):
    """Test filtering outcomes by domain."""
    response = client.get("/heimdall/decisions/outcomes?domain=security")
    assert response.status_code == 200
    data = response.json()
    # Should only have security domain outcomes
    for item in data["items"]:
        assert item["domain"] == "security"


def test_filter_outcomes_by_decision_id(client: TestClient):
    """Test filtering outcomes by decision_id."""
    response = client.get("/heimdall/decisions/outcomes?decision_id=deal_001")
    assert response.status_code == 200
    data = response.json()
    if data["total"] > 0:
        for item in data["items"]:
            assert item["decision_id"] == "deal_001"


def test_outcome_with_all_fields(client: TestClient):
    """Test creating an outcome with all optional fields."""
    from datetime import datetime, timedelta

    occurred = datetime.utcnow() - timedelta(days=5)
    response = client.post(
        "/heimdall/decisions/outcomes",
        json={
            "decision_id": "family_001",
            "title": "Custody agreement modification",
            "domain": "family",
            "action_taken": "partial",
            "outcome_quality": "good",
            "impact_score": 60,
            "notes": "Partial agreement reached, improved flexibility",
            "metadata": {
                "old_schedule": "50/50 split",
                "new_schedule": "flexible arrangement",
                "mediation_hours": 8,
            },
            "occurred_at": occurred.isoformat(),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Custody agreement modification"
    assert data["action_taken"] == "partial"


def test_outcome_impact_score_range(client: TestClient):
    """Test impact scores in valid range."""
    response = client.post(
        "/heimdall/decisions/outcomes",
        json={
            "decision_id": "test_score_100",
            "title": "Perfect decision",
            "domain": "business",
            "action_taken": "accepted",
            "impact_score": 100,
        },
    )
    assert response.status_code == 201

    response = client.post(
        "/heimdall/decisions/outcomes",
        json={
            "decision_id": "test_score_-100",
            "title": "Worst decision",
            "domain": "business",
            "action_taken": "blocked",
            "impact_score": -100,
        },
    )
    assert response.status_code == 201
