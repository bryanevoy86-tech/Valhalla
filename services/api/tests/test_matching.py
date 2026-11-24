"""
Tests for buyer matching engine - roundtrip with scoring.
"""

import json



def test_match_flow(legacy_http_client):
    client, _ = legacy_http_client
    """Test complete buyer-deal matching workflow with scoring."""
    # Create buyer
    b = {
        "name": "Winnipeg SFH Buyer",
        "regions": "Winnipeg,CA-MB",
        "property_types": "SFH,Duplex",
        "min_price": 100000,
        "max_price": 350000,
        "min_beds": 3,
        "min_baths": 1,
        "tags": "garage,corner lot"
    }
    r = client.post("/api/buyers", data=json.dumps(b))
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    buyer_id = r.json()["id"]

    # Create deal
    d = {
        "headline": "SFH in Transcona with garage",
        "region": "Winnipeg",
        "property_type": "SFH",
        "price": 289000,
        "beds": 3,
        "baths": 1,
        "notes": "solid bones"
    }
    r = client.post("/api/deals", data=json.dumps(d))
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    deal_id = r.json()["id"]

    # Compute matches (deal -> buyers)
    r = client.post(
        "/api/match/compute",
        data=json.dumps({"deal_id": deal_id, "min_score": 0.25}),
        timeout=10
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    hits = r.json()["hits"]
    assert len(hits) >= 1, f"Expected at least 1 hit, got {len(hits)}"
    assert hits[0]["score"] >= 0.25, f"Expected score >= 0.25, got {hits[0]['score']}"

    # Buyer -> deals
    r = client.post(
        "/api/match/compute",
        data=json.dumps({"buyer_id": buyer_id, "min_score": 0.25}),
        timeout=10
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    hits = r.json()["hits"]
    assert len(hits) >= 1, f"Expected at least 1 hit, got {len(hits)}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
