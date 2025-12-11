"""
PACK CI4: Insight Synthesizer Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_create_insight(client):
    """Test creating an insight"""
    payload = {
        "source": "heimdall",
        "category": "finance",
        "title": "Cash flow optimization opportunity",
        "body": "You are holding 15% excess cash. Consider deploying in short-term investments.",
        "importance": 7,
        "tags": {"type": "cash_management", "urgency": "medium"},
    }
    
    r = client.post("/intelligence/insights/", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Cash flow optimization opportunity"
    assert body["importance"] == 7


def test_create_system_insight(client):
    """Test creating a system insight"""
    payload = {
        "source": "system",
        "category": "system",
        "title": "Database performance degradation",
        "body": "Query response times have increased 40% over the past week.",
        "importance": 9,
        "context": {
            "metric": "query_latency_ms",
            "current": 450,
            "baseline": 320,
        },
    }
    
    r = client.post("/intelligence/insights/", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "system"
    assert body["importance"] == 9


def test_list_all_insights(client):
    """Test listing all insights"""
    # Create multiple insights
    insights = [
        {
            "source": "heimdall",
            "category": "finance",
            "title": "Insight 1",
            "body": "Body 1",
            "importance": 5,
        },
        {
            "source": "system",
            "category": "security",
            "title": "Insight 2",
            "body": "Body 2",
            "importance": 8,
        },
        {
            "source": "manual",
            "category": "family",
            "title": "Insight 3",
            "body": "Body 3",
            "importance": 3,
        },
    ]
    
    for insight in insights:
        client.post("/intelligence/insights/", json=insight)
    
    # List all
    r = client.get("/intelligence/insights/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3


def test_filter_insights_by_category(client):
    """Test filtering insights by category"""
    insights = [
        {
            "source": "heimdall",
            "category": "finance",
            "title": "Finance insight",
            "body": "Body",
            "importance": 5,
        },
        {
            "source": "system",
            "category": "security",
            "title": "Security insight",
            "body": "Body",
            "importance": 5,
        },
    ]
    
    for insight in insights:
        client.post("/intelligence/insights/", json=insight)
    
    # Filter by category
    r = client.get("/intelligence/insights/?category=finance")
    assert r.status_code == 200
    body = r.json()
    assert all(item["category"] == "finance" for item in body["items"])


def test_filter_by_minimum_importance(client):
    """Test filtering insights by minimum importance"""
    insights = [
        {
            "source": "heimdall",
            "category": "test",
            "title": "Critical",
            "body": "Body",
            "importance": 10,
        },
        {
            "source": "heimdall",
            "category": "test",
            "title": "Low priority",
            "body": "Body",
            "importance": 2,
        },
    ]
    
    for insight in insights:
        client.post("/intelligence/insights/", json=insight)
    
    # Only high importance
    r = client.get("/intelligence/insights/?min_importance=8")
    assert r.status_code == 200
    body = r.json()
    assert all(item["importance"] >= 8 for item in body["items"])


def test_insights_sorted_by_importance_and_recency(client):
    """Test that insights are sorted by importance (desc) then created_at (desc)"""
    insights = [
        {
            "source": "heimdall",
            "category": "test",
            "title": "Importance 5",
            "body": "Body",
            "importance": 5,
        },
        {
            "source": "heimdall",
            "category": "test",
            "title": "Importance 9",
            "body": "Body",
            "importance": 9,
        },
        {
            "source": "heimdall",
            "category": "test",
            "title": "Importance 7",
            "body": "Body",
            "importance": 7,
        },
    ]
    
    for insight in insights:
        client.post("/intelligence/insights/", json=insight)
    
    r = client.get("/intelligence/insights/")
    body = r.json()
    
    # Should be sorted by importance descending
    importances = [item["importance"] for item in body["items"]]
    assert importances == sorted(importances, reverse=True)


def test_insight_default_values(client):
    """Test that insights use default values correctly"""
    payload = {
        "category": "test",
        "title": "Test insight",
        "body": "Test body",
    }
    
    r = client.post("/intelligence/insights/", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "heimdall"  # default
    assert body["importance"] == 5  # default
    assert body["tags"] is None
    assert body["context"] is None
