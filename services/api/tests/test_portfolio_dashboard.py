# services/api/tests/test_portfolio_dashboard.py

from __future__ import annotations

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Adjust if your main import path is different
from app.main import app  # or: from valhalla.services.api.main import app
from app.core.db import get_db

client = TestClient(app)


def mock_db_override():
    """
    Override get_db dependency to return a mocked database session.
    """
    mock_db = MagicMock()
    
    # Mock query results
    mock_db.query.return_value.all.return_value = []
    mock_db.query.return_value.filter.return_value.all.return_value = []
    
    try:
        yield mock_db
    finally:
        pass


def test_portfolio_summary_endpoint():
    """
    Test portfolio summary with mocked database queries.
    """
    app.dependency_overrides[get_db] = mock_db_override
    
    try:
        resp = client.get("/api/portfolio/summary")
        assert resp.status_code == 200, resp.text

        data = resp.json()
        assert "total_deals" in data
        assert "status_counts" in data
        assert "freeze_counts" in data

        status_counts = data["status_counts"]
        assert "active" in status_counts
        assert data["total_deals"] >= 0
    finally:
        app.dependency_overrides.clear()


def test_portfolio_deals_endpoint():
    """
    Test portfolio deals endpoint with mocked database queries.
    """
    app.dependency_overrides[get_db] = mock_db_override
    
    try:
        resp = client.get("/api/portfolio/deals")
        assert resp.status_code == 200, resp.text

        data = resp.json()
        assert "summary" in data
        assert "deals" in data

        deals = data["deals"]
        assert isinstance(deals, list)
    finally:
        app.dependency_overrides.clear()
