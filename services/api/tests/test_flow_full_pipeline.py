# services/api/tests/test_flow_full_pipeline.py

from __future__ import annotations

from fastapi.testclient import TestClient

# Adjust this import if your app is exposed differently
from app.main import app  # or from valhalla.services.api.main import app


client = TestClient(app)


def test_full_deal_pipeline_happy_path():
    """
    Happy path for the full deal pipeline:

    - Creates lead
    - Creates DealBrief
    - Creates backend Deal
    - Runs underwriting (should pass)
    - Matches at least one buyer (assuming buyers seeded elsewhere)
    """

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
            "min_match_score": 0.0,  # allow even weak matches for this test
            "max_results": 10,
        },
        "underwriting": {
            "arv": 325000,
            "purchase_price": 240000,
            "repairs": 42000,
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
    assert "lead" in data
    assert "deal" in data
    assert "backend_deal_id" in data
    assert "underwriting_result" in data
    assert "matched_buyers" in data
    assert "freeze_event_created" in data
    assert "metadata" in data

    lead = data["lead"]
    deal = data["deal"]
    uw = data["underwriting_result"]
    matches = data["matched_buyers"]
    backend_deal_id = data["backend_deal_id"]

    # Lead basics
    assert lead["name"] == "John Seller"
    assert lead["id"] is not None

    # Deal basics
    assert deal["headline"].startswith("SFH in Transcona")
    assert deal["id"] is not None

    # Backend deal id present
    assert isinstance(backend_deal_id, int)
    assert backend_deal_id > 0

    # Underwriting should have metrics and a recommendation
    assert "metrics" in uw
    assert "recommendation" in uw
    assert uw["metrics"]["total_project_cost"] > 0

    # No mandatory freeze in the happy path, but allow either
    assert isinstance(data["freeze_event_created"], bool)


def test_full_deal_pipeline_bad_underwriting_triggers_freeze():
    """
    Failure underwriting case:

    - Numbers chosen to violate policy (high LTV, low equity/ROI)
    - Should still create lead + deal + backend deal
    - Should set freeze_event_created = True
    """

    payload = {
        "lead": {
            "name": "Jane Distress",
            "email": "jane@example.com",
            "phone": "555-8888",
            "source": "Direct Mail",
            "address": "999 Overpriced Ave, Winnipeg, MB",
            "tags": "distressed,high_ltv",
            "org_id": 1,
        },
        "deal": {
            "headline": "Overpriced SFH with heavy repairs",
            "region": "Winnipeg",
            "property_type": "SFH",
            "price": 310000,
            "beds": 3,
            "baths": 2,
            "notes": "Structurally questionable, big rehab needed",
            "status": "active",
            "arv": 320000,
            "repairs": 60000,
            "offer": 305000,
            "mao": 310000,
            "roi_note": "Likely fails underwriting",
        },
        "match_settings": {
            "match_buyers": False,
            "min_match_score": 0.7,
            "max_results": 5,
        },
        "underwriting": {
            "arv": 320000,
            "purchase_price": 305000,
            "repairs": 60000,
            "closing_costs": 12000,
            "holding_months": 12,
            "monthly_taxes": 400,
            "monthly_insurance": 200,
            "monthly_utilities": 250,
            "monthly_hoa": 150,
            "monthly_other": 200,
            "expected_rent": 1500,
            "policy": None,
        },
    }

    response = client.post("/flow/full_deal_pipeline", json=payload)
    assert response.status_code == 201, response.text

    data = response.json()
    uw = data["underwriting_result"]
    flags = uw["flags"]

    # We expect at least one policy breach with these numbers
    assert (
        flags["breach_ltv"]
        or flags["breach_roi"]
        or flags["breach_equity"]
    ), "Expected at least one underwriting policy breach."

    # And the pipeline should record a freeze event
    assert data["freeze_event_created"] is True
