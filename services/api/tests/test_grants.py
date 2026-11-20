"""
Tests for grants endpoints - roundtrip test with scoring.
"""

import json
import datetime as dt



def test_grants_roundtrip(legacy_http_client):
    client, _ = legacy_http_client
    """Test complete grants workflow: add source, add grant, generate pack."""
    # Add source
    s = {
        "name": "MB Self-Employment Program",
        "url": "https://gov.mb.ca",
        "region": "CA-MB",
        "tags": "EIA,startup"
    }
    r = client.post("/grants/sources", data=json.dumps(s))
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    sid = r.json()["id"]
    
    # Add grant
    g = {
        "source_id": sid,
        "title": "Startup Training Support",
        "program": "EIA Self-Employment",
        "category": "training",
        "region": "CA-MB",
        "amount_min": 500.00,
        "amount_max": 5000.00,
        "deadline": (dt.date.today().replace(day=28)).isoformat(),
        "link": "https://gov.mb.ca/eia",
        "summary": "Support for approved training expenses"
    }
    r = client.post("/grants", data=json.dumps(g))
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    
    # Generate pack
    crit = {
        "region": "CA-MB",
        "categories": ["training"],
        "min_amount": 100,
        "limit": 10
    }
    r = client.post("/grants/generate", data=json.dumps(crit))
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    
    j = r.json()
    assert j["total"] >= 1, f"Expected at least 1 grant, got {j['total']}"
    assert j["hits"][0]["score"] >= 0.5, f"Expected score >= 0.5, got {j['hits'][0]['score']}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
