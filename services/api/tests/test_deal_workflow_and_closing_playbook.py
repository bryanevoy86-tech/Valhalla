# services/api/tests/test_deal_workflow_and_closing_playbook.py

from __future__ import annotations

from fastapi.testclient import TestClient

# Adjust this import if needed
from app.main import app  # or: from valhalla.services.api.main import app

client = TestClient(app)


def _create_pipeline_deal_for_status() -> int:
    """
    Create a deal via the full pipeline so we can test downstream endpoints.
    """
    payload = {
        "lead": {
            "name": "Status Seller",
            "email": "status-seller@example.com",
            "phone": "555-2222",
            "source": "Referral",
            "address": "321 Status Ave, Winnipeg, MB",
            "tags": "test,status",
            "org_id": 1,
        },
        "deal": {
            "headline": "Status SFH in Transcona",
            "region": "Winnipeg",
            "property_type": "SFH",
            "price": 300000,
            "beds": 3,
            "baths": 2,
            "notes": "Used for workflow + closing playbook tests.",
            "status": "active",
            "arv": 350000,
            "repairs": 30000,
            "offer": 250000,
            "mao": 260000,
            "roi_note": "Test ROI note.",
        },
        "match_settings": {
            "match_buyers": False,
            "min_match_score": 0.5,
            "max_results": 5,
        },
        "underwriting": {
            "arv": 350000,
            "purchase_price": 250000,
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


def test_deal_workflow_status_endpoint():
    backend_deal_id = _create_pipeline_deal_for_status()

    response = client.get(f"/workflow/deal_status/{backend_deal_id}")
    assert response.status_code == 200, response.text

    data = response.json()
    assert "deal" in data
    assert "lead" in data or data["lead"] is None
    assert "deal_brief" in data or data["deal_brief"] is None
    assert "freeze" in data
    assert "buyer_readiness" in data
    assert "flags" in data

    deal = data["deal"]
    assert deal["id"] == backend_deal_id
    assert deal["status"] in {"draft", "active", "under_contract", "sold", "archived"}


def test_closing_playbook_endpoint():
    backend_deal_id = _create_pipeline_deal_for_status()

    response = client.get(f"/flow/closing_playbook/{backend_deal_id}")
    assert response.status_code == 200, response.text

    data = response.json()
    assert "context" in data
    assert "script" in data

    context = data["context"]
    script = data["script"]

    # Context basics
    assert "lead" in context
    assert "deal" in context
    assert "buyers" in context
    assert "freeze" in context
    assert "underwriting" in context
    assert "suggested_opening" in context

    lead = context["lead"]
    deal = context["deal"]

    assert lead["id"] is not None
    assert lead["name"]
    assert deal["backend_deal_id"] == backend_deal_id

    # Script sections should be present
    assert "opening" in script
    assert "rapport_questions" in script
    assert "diagnostic_questions" in script
    assert "numbers_framing" in script
    assert "offer_framing" in script
    assert "objection_prompts" in script
    assert "closing_prompts" in script
    assert "summary_for_ai" in script

    # And the opening line should not be empty
    assert script["opening"]
