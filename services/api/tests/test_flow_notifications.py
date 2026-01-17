# services/api/tests/test_flow_notifications.py

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Adjust this import if your app is exposed differently
from app.main import app  # or: from valhalla.services.api.main import app

from app.core.db import get_db
from app.models.match import Buyer

client = TestClient(app)


def _seed_matching_buyer(db: Session) -> Buyer:
    """
    Seed a buyer that should match a typical Winnipeg SFH deal
    so notifications have someone to target.
    """
    buyer = Buyer(
        name="Notification Test Buyer",
        email="notif-buyer@example.com",
        phone="555-4444",
        regions="Winnipeg, Brandon",
        property_types="SFH, Duplex",
        min_price=Decimal("200000"),
        max_price=Decimal("400000"),
        min_beds=3,
        min_baths=2,
        tags="test,notifications",
        active=True,
    )
    db.add(buyer)
    db.commit()
    db.refresh(buyer)
    return buyer


def _create_pipeline_deal() -> int:
    """
    Run the full pipeline once and return backend_deal_id.
    Assumes /flow/full_deal_pipeline is wired correctly.
    """
    payload = {
        "lead": {
            "name": "Notify Seller",
            "email": "notify-seller@example.com",
            "phone": "555-1111",
            "source": "PPC",
            "address": "789 Notification St, Winnipeg, MB",
            "tags": "test,notify",
            "org_id": 1,
        },
        "deal": {
            "headline": "Notification SFH in Transcona",
            "region": "Winnipeg",
            "property_type": "SFH",
            "price": 290000,
            "beds": 3,
            "baths": 2,
            "notes": "Used for notification flow tests.",
            "status": "active",
            "arv": 340000,
            "repairs": 30000,
            "offer": 245000,
            "mao": 255000,
            "roi_note": "Comfortable margin for testing.",
        },
        "match_settings": {
            "match_buyers": False,
            "min_match_score": 0.5,
            "max_results": 5,
        },
        "underwriting": {
            "arv": 340000,
            "purchase_price": 245000,
            "repairs": 30000,
            "closing_costs": 8000,
            "holding_months": 6,
            "monthly_taxes": 300,
            "monthly_insurance": 150,
            "monthly_utilities": 200,
            "monthly_hoa": 0,
            "monthly_other": 100,
            "expected_rent": 2200,
            "policy": None,
        },
    }

    response = client.post("/flow/full_deal_pipeline", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    backend_deal_id = data.get("backend_deal_id")
    assert isinstance(backend_deal_id, int) and backend_deal_id > 0
    return backend_deal_id


def test_notify_deal_parties_seller_and_buyers():
    # Seed buyer + create deal
    db_gen = get_db()
    db: Session = next(db_gen)
    _seed_matching_buyer(db)

    backend_deal_id = _create_pipeline_deal()

    payload = {
        "backend_deal_id": backend_deal_id,
        "include_seller": True,
        "include_buyers": True,
        "min_buyer_score": 0.0,  # allow any seeded buyer to pass
        "max_buyers": 10,
    }

    response = client.post("/flow/notify_deal_parties", json=payload)
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["backend_deal_id"] == backend_deal_id

    # Seller notification should exist and have basic structure
    seller = data.get("seller_notification")
    assert seller is not None
    assert seller["subject"]
    assert "body_text" in seller
    # Email is optional, but for this test we provided one
    # so we expect it to be present.
    assert seller["to_email"] == "notify-seller@example.com"

    # Buyer notifications should include at least one entry
    buyers = data.get("buyer_notifications", [])
    assert isinstance(buyers, list)
    assert len(buyers) >= 1

    first = buyers[0]
    assert "buyer_id" in first
    assert "subject" in first
    assert "body_text" in first
    assert "match_score" in first
