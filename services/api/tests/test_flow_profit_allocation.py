# services/api/tests/test_flow_profit_allocation.py

from __future__ import annotations

from fastapi.testclient import TestClient

# Adjust this import if your app is exposed differently
from app.main import app  # or: from valhalla.services.api.main import app

client = TestClient(app)


def _create_pipeline_deal_for_profit() -> int:
    """
    Use the full pipeline to create a deal with known numbers,
    then run profit allocation on it.
    """
    payload = {
        "lead": {
            "name": "Profit Seller",
            "email": "profit-seller@example.com",
            "phone": "555-3333",
            "source": "PPC",
            "address": "987 Profit St, Winnipeg, MB",
            "tags": "test,profit",
            "org_id": 1,
        },
        "deal": {
            "headline": "Profit SFH in Transcona",
            "region": "Winnipeg",
            "property_type": "SFH",
            "price": 280000,
            "beds": 3,
            "baths": 2,
            "notes": "Used for profit allocation tests.",
            "status": "active",
            "arv": 340000,
            "repairs": 30000,
            "offer": 240000,
            "mao": 250000,
            "roi_note": "Healthy profit scenario.",
        },
        "match_settings": {
            "match_buyers": False,
            "min_match_score": 0.5,
            "max_results": 5,
        },
        "underwriting": {
            "arv": 340000,
            "purchase_price": 240000,
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


def test_profit_allocation_happy_path():
    backend_deal_id = _create_pipeline_deal_for_profit()

    payload = {
        "profit": {
            "backend_deal_id": backend_deal_id,
            "sale_price": 340000,
            "sale_closing_costs": 10000,
            "extra_expenses": 5000,
            "tax_rate": 0.25,
            "funfunds_percent": 0.15,
            "reinvest_percent": 0.50,
        },
        "policy": None,
    }

    response = client.post("/flow/profit_allocation", json=payload)
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["backend_deal_id"] == backend_deal_id

    result = data["result"]
    metrics = result["metrics"]
    breakdown = result["breakdown"]
    flags = result["flags"]

    # Basic sanity checks
    assert metrics["sale_price"] == 340000
    assert metrics["gross_profit"] is not None
    assert metrics["net_profit_after_tax"] is not None

    assert breakdown["funfunds_amount"] >= 0
    assert breakdown["reinvest_amount"] >= 0
    assert breakdown["owner_draw_amount"] >= 0

    # In this happy path we don't expect policy breaches
    assert flags["breach_min_tax_rate"] is False
    assert flags["breach_funfunds_cap"] is False
    assert flags["breach_min_reinvest"] is False


def test_profit_allocation_policy_breach_triggers_freeze_flag():
    backend_deal_id = _create_pipeline_deal_for_profit()

    # Deliberately low tax rate & high FunFunds to breach policy
    payload = {
        "profit": {
            "backend_deal_id": backend_deal_id,
            "sale_price": 340000,
            "sale_closing_costs": 5000,
            "extra_expenses": 2000,
            "tax_rate": 0.05,           # below default min_tax_rate 0.20
            "funfunds_percent": 0.40,   # above default max_funfunds_percent 0.25
            "reinvest_percent": 0.10,   # below default min_reinvest_percent 0.30
        },
        "policy": None,
    }

    response = client.post("/flow/profit_allocation", json=payload)
    assert response.status_code == 200, response.text

    data = response.json()
    result = data["result"]
    flags = result["flags"]

    assert (
        flags["breach_min_tax_rate"]
        or flags["breach_funfunds_cap"]
        or flags["breach_min_reinvest"]
    )

    # When policy is breached, we expect freeze_event_created to be True
    assert data["freeze_event_created"] is True
