# services/api/tests/test_flow_lead_to_deal.py

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app  # FastAPI instance
from app.core.db import get_db
from app.models.match import Buyer

client = TestClient(app)


def _seed_test_buyer(db: Session) -> Buyer:
    """Seed a test buyer that matches our test deal criteria."""
    buyer = Buyer(
        name="Test Buyer",
        email="buyer@example.com",
        phone="555-9999",
        regions="winnipeg, brandon",
        property_types="sfh, duplex",
        min_price=Decimal("200000"),
        max_price=Decimal("350000"),
        min_beds=3,
        min_baths=2,
        tags="test,buyer",
        active=True,
    )
    db.add(buyer)
    db.commit()
    db.refresh(buyer)
    return buyer


def test_flow_lead_to_deal_basic():
    """Test the complete lead-to-deal flow with buyer matching."""
    # Get a DB session from the app dependency
    db_gen = get_db()
    db = next(db_gen)

    # Seed at least one buyer that should match the test deal
    test_buyer = _seed_test_buyer(db)

    payload = {
        "lead": {
            "name": "John Seller",
            "email": "john@example.com",
            "phone": "555-1234",
            "source": "Facebook",
            "address": "123 Main St, Winnipeg, MB",
            "tags": "motivated,sfh",
            "org_id": 1,
        },
        "deal": {
            "headline": "SFH in Transcona - solid bones",
            "region": "Winnipeg",
            "property_type": "SFH",
            "price": 285000,
            "beds": 3,
            "baths": 2,
            "notes": "Tenant in place, needs cosmetic reno",
            "status": "active",
            "arv": 325000,
            "repairs": 42000,
            "offer": 240000,
            "mao": 250000,
            "roi_note": "Standard BRRRR thresholds",
        },
        "match_settings": {
            "match_buyers": True,
            "min_match_score": 0.7,
            "max_results": 10,
        },
    }

    response = client.post("/api/flow/lead_to_deal", json=payload)
    assert response.status_code == 201, response.text

    data = response.json()
    assert "lead" in data
    assert "deal" in data
    assert "matched_buyers" in data
    assert "metadata" in data

    lead = data["lead"]
    deal = data["deal"]
    matches = data["matched_buyers"]
    meta = data["metadata"]

    # Basic sanity checks
    assert lead["name"] == "John Seller"
    assert deal["headline"].startswith("SFH in Transcona")

    # IDs present in metadata
    assert meta.get("lead_id") is not None
    assert meta.get("deal_brief_id") is not None
    assert meta.get("backend_deal_id") is not None

    # With our seeded buyer, we expect at least one match
    assert len(matches) >= 1, "Expected at least one buyer match"
    assert matches[0]["score"] >= 0.7, "Expected score >= 0.7"
    assert matches[0]["buyer_id"] == test_buyer.id

    # Cleanup
    db.delete(test_buyer)
    db.commit()

    print(f"✅ Flow test passed: Created lead {meta['lead_id']}, "
          f"deal brief {meta['deal_brief_id']}, backend deal {meta['backend_deal_id']}, "
          f"matched {len(matches)} buyers")


def test_flow_lead_to_deal_no_buyers():
    """Test flow when no buyers match."""
    # Get a DB session
    db_gen = get_db()
    db = next(db_gen)

    payload = {
        "lead": {
            "name": "Jane Seller",
            "email": "jane@example.com",
            "phone": "555-5678",
            "source": "Referral",
            "org_id": 1,
        },
        "deal": {
            "headline": "Commercial Property in Rural Area",
            "region": "Remote",
            "property_type": "Commercial",
            "price": 5000000,  # Way above any buyer's max
            "beds": 0,
            "baths": 0,
            "status": "active",
            "arv": 5500000,
            "repairs": 100000,
            "offer": 4500000,
            "mao": 4800000,
        },
        "match_settings": {
            "match_buyers": True,
            "min_match_score": 0.7,
            "max_results": 10,
        },
    }

    response = client.post("/api/flow/lead_to_deal", json=payload)
    assert response.status_code == 201, response.text

    data = response.json()
    matches = data["matched_buyers"]

    # Should have no matches
    assert len(matches) == 0, "Expected zero buyer matches for overpriced commercial property"
    assert "No buyers matched" in data["notes"]

    print("✅ No-match test passed")


def test_flow_lead_to_deal_matching_disabled():
    """Test flow when buyer matching is disabled."""
    payload = {
        "lead": {
            "name": "Bob Seller",
            "email": "bob@example.com",
            "phone": "555-9876",
            "source": "LinkedIn",
            "org_id": 1,
        },
        "deal": {
            "headline": "Fixer Upper",
            "region": "Toronto",
            "property_type": "Condo",
            "price": 400000,
            "beds": 2,
            "baths": 1,
            "status": "active",
            "arv": 480000,
            "repairs": 60000,
            "offer": 350000,
            "mao": 380000,
        },
        "match_settings": {
            "match_buyers": False,  # Disable matching
            "min_match_score": 0.7,
            "max_results": 10,
        },
    }

    response = client.post("/api/flow/lead_to_deal", json=payload)
    assert response.status_code == 201, response.text

    data = response.json()
    matches = data["matched_buyers"]

    # Should have no matches because matching was disabled
    assert len(matches) == 0
    assert "matching was disabled" in data["notes"]

    print("✅ Matching-disabled test passed")


if __name__ == "__main__":
    print("Running flow_lead_to_deal tests...")
    test_flow_lead_to_deal_basic()
    test_flow_lead_to_deal_no_buyers()
    test_flow_lead_to_deal_matching_disabled()
    print("\n✅ All tests passed!")
