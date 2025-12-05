# services/api/tests/test_closer_engine_flow.py

from __future__ import annotations

from fastapi.testclient import TestClient

# Adjust this import if your app is exposed differently
from app.main import app  # or: from valhalla.services.api.main import app

client = TestClient(app)


def _create_pipeline_deal_for_closer() -> int:
    """
    Create a deal via the full pipeline so the closer has something real to work on.
    """
    payload = {
        "lead": {
            "name": "Closer Seller",
            "email": "closer-seller@example.com",
            "phone": "555-9999",
            "source": "PPC",
            "address": "111 Closer St, Winnipeg, MB",
            "tags": "test,closer",
            "org_id": 1,
        },
        "deal": {
            "headline": "Closer SFH in Transcona",
            "region": "Winnipeg",
            "property_type": "SFH",
            "price": 290000,
            "beds": 3,
            "baths": 2,
            "notes": "Used for closer engine tests.",
            "status": "active",
            "arv": 340000,
            "repairs": 30000,
            "offer": 245000,
            "mao": 255000,
            "roi_note": "Healthy margin.",
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

    resp = client.post("/flow/full_deal_pipeline", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    backend_deal_id = data.get("backend_deal_id")
    assert isinstance(backend_deal_id, int) and backend_deal_id > 0
    return backend_deal_id


def test_closer_start_and_next_blocks_and_feedback():
    backend_deal_id = _create_pipeline_deal_for_closer()

    # Start session
    start_payload = {
        "backend_deal_id": backend_deal_id,
        "channel": "phone",
        "role": "acquisition",
    }
    resp = client.post("/closer/start", json=start_payload)
    assert resp.status_code == 200, resp.text

    start_data = resp.json()
    session_id = start_data["session_id"]
    assert session_id
    assert start_data["backend_deal_id"] == backend_deal_id
    assert "opening_line" in start_data
    assert "first_prompts" in start_data

    # Request next block after rapport
    next_payload = {
        "session_id": session_id,
        "backend_deal_id": backend_deal_id,
        "last_section": "rapport",
        "outcome": "Seller is open to talking.",
    }
    resp_next = client.post("/closer/next_block", json=next_payload)
    assert resp_next.status_code == 200, resp_next.text

    next_data = resp_next.json()
    assert next_data["session_id"] == session_id
    assert next_data["backend_deal_id"] == backend_deal_id
    assert "next_section" in next_data
    assert "prompts" in next_data
    assert isinstance(next_data["prompts"], list)

    # Record feedback
    feedback_payload = {
        "session_id": session_id,
        "backend_deal_id": backend_deal_id,
        "disposition": "maybe",
        "reason": "Seller wants to think it over.",
        "next_steps": "Follow up in 3 days.",
    }
    resp_fb = client.post("/closer/feedback", json=feedback_payload)
    assert resp_fb.status_code == 200, resp_fb.text

    fb_data = resp_fb.json()
    assert fb_data["stored"] is True

    # Transcript stub
    resp_tx = client.get(f"/closer/transcript/{session_id}")
    assert resp_tx.status_code == 200, resp_tx.text

    tx_data = resp_tx.json()
    assert tx_data["session_id"] == session_id
    assert tx_data["backend_deal_id"] == backend_deal_id
    assert tx_data["status"] == "stub"
