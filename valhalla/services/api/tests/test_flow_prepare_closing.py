# services/api/tests/test_flow_prepare_closing.py

from __future__ import annotations

from fastapi.testclient import TestClient

# Adjust this import if your app is exposed differently
from app.main import app  # or: from valhalla.services.api.main import app

client = TestClient(app)


def _create_pipeline_deal() -> int:
    """
    Helper: runs the full pipeline once and returns backend_deal_id.
    Assumes /flow/full_deal_pipeline is wired correctly.
    """
    payload = {
        "lead": {
            "name": "Context Seller",
            "email": "context@example.com",
            "phone": "555-7777",
            "source": "PPC",
            "address": "456 Pipeline St, Winnipeg, MB",
            "tags": "test,closing_context",
            "org_id": 1,
        },
        "deal": {
            "headline": "Context SFH in Transcona",
            "region": "Winnipeg",
            "property_type": "SFH",
            "price": 295000,
            "beds": 3,
            "baths": 2,
            "notes": "Used to test closing context.",
            "status": "active",
            "arv": 340000,
            "repairs": 35000,
            "offer": 250000,
            "mao": 260000,
            "roi_note": "Healthy spread for testing.",
        },
        "match_settings": {
            "match_buyers": False,
            "min_match_score": 0.5,
            "max_results": 5,
        },
        "underwriting": {
            "arv": 340000,
            "purchase_price": 250000,
            "repairs": 35000,
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


def test_closing_context_basic():
    backend_deal_id = _create_pipeline_deal()

    response = client.get(f"/flow/closing_context/{backend_deal_id}")
    assert response.status_code == 200, response.text

    data = response.json()
    assert "lead" in data
    assert "deal" in data
    assert "buyers" in data
    assert "freeze" in data
    assert "underwriting" in data
    assert "suggested_opening" in data

    lead = data["lead"]
    deal = data["deal"]
    freeze = data["freeze"]

    # Lead basics
    assert lead["id"] is not None
    assert lead["name"]  # should not be empty

    # Deal basics
    assert deal["backend_deal_id"] == backend_deal_id
    assert deal["status"] in {"draft", "active", "under_contract", "sold", "archived"}

    # Freeze summary should be present with flags
    assert "has_freeze" in freeze
    assert "count" in freeze
