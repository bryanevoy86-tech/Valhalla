"""
PACK CI2: Opportunity Engine Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_create_opportunity(client):
    """Test creating an opportunity"""
    payload = {
        "source_type": "deal",
        "source_id": "deal_12345",
        "title": "Warehouse acquisition in Toronto",
        "description": "2000 sqft industrial space, below market value",
        "value_score": 8.5,
        "effort_score": 6.0,
        "risk_score": 4.0,
        "roi_score": 7.5,
        "time_horizon_days": 90,
        "tags": {"market": "real_estate", "urgency": "high"},
    }
    
    r = client.post("/intelligence/opportunities/", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Warehouse acquisition in Toronto"
    assert body["active"] is True


def test_update_opportunity(client):
    """Test updating existing opportunity (idempotent)"""
    payload = {
        "source_type": "grant",
        "source_id": "grant_xyz",
        "title": "Government innovation grant",
        "value_score": 5.0,
    }
    
    # Create first time
    r1 = client.post("/intelligence/opportunities/", json=payload)
    assert r1.status_code == 200
    opp1 = r1.json()
    
    # Update same opportunity
    payload["value_score"] = 7.0
    r2 = client.post("/intelligence/opportunities/", json=payload)
    assert r2.status_code == 200
    opp2 = r2.json()
    
    # Should be same ID
    assert opp2["id"] == opp1["id"]
    assert opp2["value_score"] == 7.0


def test_list_opportunities(client):
    """Test listing opportunities with filtering"""
    # Create multiple opportunities
    opportunities = [
        {
            "source_type": "deal",
            "source_id": "d1",
            "title": "Deal 1",
            "value_score": 9.0,
            "roi_score": 8.0,
        },
        {
            "source_type": "content",
            "source_id": "c1",
            "title": "Content 1",
            "value_score": 6.0,
            "roi_score": 5.0,
        },
        {
            "source_type": "deal",
            "source_id": "d2",
            "title": "Deal 2",
            "value_score": 7.0,
            "roi_score": 7.0,
            "active": False,
        },
    ]
    
    for opp in opportunities:
        client.post("/intelligence/opportunities/", json=opp)
    
    # List all active
    r = client.get("/intelligence/opportunities/?active_only=true")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    
    # Filter by source_type
    r = client.get("/intelligence/opportunities/?source_type=deal&active_only=true")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    
    # Sorted by value_score and roi_score
    assert body["items"][0]["title"] == "Deal 1"


def test_list_inactive_opportunities(client):
    """Test listing inactive opportunities"""
    payload = {
        "source_type": "shipwreck",
        "source_id": "ship_001",
        "title": "Old opportunity",
        "active": False,
    }
    
    client.post("/intelligence/opportunities/", json=payload)
    
    # Active only should not include it
    r = client.get("/intelligence/opportunities/?active_only=true")
    assert r.status_code == 200
    body = r.json()
    
    # All should include it
    r = client.get("/intelligence/opportunities/?active_only=false")
    assert r.status_code == 200
    body = r.json()
    assert any(o["title"] == "Old opportunity" for o in body["items"])
