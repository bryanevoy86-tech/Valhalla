# services/api/tests/test_flow_full_pipeline.py

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.db import get_db
from app.leads.models import Lead
from app.models.deal import Deal, DealBriefLink
from app.models.freeze_events import FreezeEvent
from app.models.match import Buyer, DealBrief
from app.offers.models import Offer
from app.routers.deal_workflow_status import router as workflow_router
from app.routers.flow_full_pipeline import router as flow_router


@pytest.fixture
def fixture(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for model in (Lead, DealBrief, Deal, DealBriefLink, Buyer, FreezeEvent, Offer):
        model.__table__.create(engine)
    with Session(engine) as db:
        db.add(DealBrief(id=1, headline="Existing unrelated brief"))
        db.add(Buyer(name="Scoped test buyer", regions="Winnipeg", property_types="SFH"))
        db.commit()

    api = FastAPI()
    api.include_router(flow_router)
    api.include_router(workflow_router)

    def isolated_db():
        with Session(engine) as db:
            yield db

    api.dependency_overrides[get_db] = isolated_db
    monkeypatch.setenv("VALHALLA_PRIME_CONTROL_KEY", "pipeline-test-prime-key")
    headers = {"X-Prime-Control-Key": "pipeline-test-prime-key"}
    try:
        with TestClient(api, headers=headers, raise_server_exceptions=False) as client:
            yield client, engine
    finally:
        engine.dispose()


def test_full_deal_pipeline_happy_path(fixture):
    """
    Happy path for the full deal pipeline:

    - Creates lead
    - Creates DealBrief
    - Creates backend Deal
    - Runs underwriting (should pass)
    - Matches at least one buyer (assuming buyers seeded elsewhere)
    """

    client, engine = fixture
    payload = {
        "lead": {
            "name": "John Seller",
            "email": "john@example.com",
            "phone": "555-010-1234",
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

    denied = client.post(
        "/flow/full_deal_pipeline", json=payload,
        headers={"X-Prime-Control-Key": "wrong"},
    )
    assert denied.status_code == 401
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
    assert Decimal(uw["metrics"]["total_project_cost"]) > 0

    assert matches[0]["name"] == "Scoped test buyer"
    assert deal["id"] != backend_deal_id
    path = f"/workflow/deal_status/{backend_deal_id}"
    assert client.get(path, headers={"X-Prime-Control-Key": "wrong"}).status_code == 401
    result = client.get(path)
    assert result.status_code == 200
    assert result.json()["deal_brief"]["id"] == deal["id"]
    assert result.json()["lead"]["id"] == lead["id"]
    assert result.json()["flags"]["ready_for_marketing"] is False

    with Session(engine) as db:
        db.delete(db.get(DealBriefLink, backend_deal_id))
        db.commit()
    assert client.get(path).json()["deal_brief"] is None


def test_full_deal_pipeline_bad_underwriting_triggers_freeze(fixture):
    """
    Failure underwriting case:

    - Numbers chosen to violate policy (high LTV, low equity/ROI)
    - Should still create lead + deal + backend deal
    - Should set freeze_event_created = True
    """

    client, engine = fixture
    payload = {
        "lead": {
            "name": "Jane Distress",
            "email": "jane@example.com",
            "phone": "555-010-8888",
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

    assert data["freeze_event_created"] is True
    deal_id = data["backend_deal_id"]
    with Session(engine) as db:
        assert db.query(FreezeEvent).filter_by(deal_id=str(deal_id)).one().notes
    state = client.get(f"/workflow/deal_status/{deal_id}").json()
    assert state["freeze"]["has_freeze"] is True
    assert state["flags"]["blocked_by_freeze"] is True

    # The pipeline must roll back the lead, Deal, DealBrief and link together
    # if the underwriting freeze cannot be persisted.
    def reject_freeze(*args):
        raise RuntimeError("injected freeze insert failure")

    event.listen(FreezeEvent, "before_insert", reject_freeze)
    try:
        assert client.post("/flow/full_deal_pipeline", json=payload).status_code == 500
    finally:
        event.remove(FreezeEvent, "before_insert", reject_freeze)
    with Session(engine) as db:
        assert db.query(Lead).count() == 1
        assert db.query(Deal).count() == 1
        assert db.query(DealBrief).count() == 2
        assert db.query(DealBriefLink).count() == 1
        assert db.query(FreezeEvent).count() == 1
