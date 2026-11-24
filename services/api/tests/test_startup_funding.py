from datetime import date, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.completion_registry import LegacyOrchestrationEvent
from app.services.startup_funding import FundingReviewIn, FundingSourceIn, review_funding, stage_funding_source


def test_dated_catalog_observation_checks_pre_registration_spend_and_owner_scope(legacy_http_client):
    client, engine = legacy_http_client
    LegacyOrchestrationEvent.__table__.create(engine, checkfirst=True)
    today = date(2026, 10, 5)
    source = client.post("/grants/sources", json={"name": "Fixture source", "url": "https://example.invalid",
                                                 "region": "CA-MB"})
    assert source.status_code == 200, source.text
    grant = client.post("/grants", json={"source_id": source.json()["id"], "title": "Fixture technology credit",
                                        "link": "https://example.invalid/program",
                                        "deadline": (today + timedelta(days=5)).isoformat()})
    assert grant.status_code == 200, grant.text
    grant_id = grant.json()["id"]
    observation = FundingSourceIn(grant_id=grant_id, source_url="https://example.invalid/program",
                                  observed_on=today, valid_through=today + timedelta(days=10),
                                  kind="TECHNOLOGY_CREDIT", currency="CAD", maximum_minor=50000,
                                  minimum_match_minor=25000, permits_unregistered=True, prior_spend_rule="PROHIBITED",
                                  eligibility_requirements=["Check permitted software."],
                                  conditions="Synthetic grant terms require application approval before spending.")
    payload = FundingReviewIn(grant_id=grant_id, available_matching_cad_minor=26000)
    unauthorized = client.post("/api/weweb/owner-startup/funding-evidence", json=observation.model_dump(mode="json"))
    assert unauthorized.status_code == 401 and unauthorized.headers["cache-control"] == "no-store"
    with Session(engine) as db:
        receipt = stage_funding_source(db, observation, 7, today)
        assert stage_funding_source(db, observation, 7, today) == receipt
        result = review_funding(db, payload, 7, today)
        assert result["source"]["sha256"] == receipt["sha256"]
        assert result["status"] == "POTENTIALLY_ELIGIBLE" and not result["verified_eligible"]
        assert result["included_in_spendable_cash_minor"] == 0 and not result["external_application_authorized"]
        early_spend = payload.model_copy(update={"intended_spend_date": today, "available_matching_cad_minor": 0})
        assert review_funding(db, early_spend, 7, today)["blockers"] == [
            "EARLY_SPEND_REQUIRES_REVIEW", "MATCHING_CAPITAL_SHORTFALL",
        ]
        with pytest.raises(HTTPException, match="No dated owner"):
            review_funding(db, payload, 8, today)
        with pytest.raises(HTTPException, match="stale"):
            review_funding(db, payload, 7, today + timedelta(days=11))
        with pytest.raises(HTTPException, match="later source date"):
            stage_funding_source(db, observation.model_copy(update={"minimum_match_minor": 0}), 7, today)
