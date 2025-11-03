"""
Tests for buyer matching engine - roundtrip with scoring.
"""

import os
import httpx
import json

API = os.getenv("API_BASE", "http://localhost:8000/api")
KEY = os.getenv("HEIMDALL_BUILDER_API_KEY", "test123")
H = {"X-API-Key": KEY, "Content-Type": "application/json"}


def test_match_flow():
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
    r = httpx.post(f"{API}/buyers", headers=H, data=json.dumps(b), timeout=10)
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
    r = httpx.post(f"{API}/deals", headers=H, data=json.dumps(d), timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    deal_id = r.json()["id"]

    # Compute matches (deal -> buyers)
    r = httpx.post(
        f"{API}/match/compute",
        headers=H,
        data=json.dumps({"deal_id": deal_id, "min_score": 0.25}),
        timeout=10
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    hits = r.json()["hits"]
    assert len(hits) >= 1, f"Expected at least 1 hit, got {len(hits)}"
    assert hits[0]["score"] >= 0.25, f"Expected score >= 0.25, got {hits[0]['score']}"

    # Buyer -> deals
    r = httpx.post(
        f"{API}/match/compute",
        headers=H,
        data=json.dumps({"buyer_id": buyer_id, "min_score": 0.25}),
        timeout=10
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    hits = r.json()["hits"]
    assert len(hits) >= 1, f"Expected at least 1 hit, got {len(hits)}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
