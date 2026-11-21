from datetime import timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.completion_registry import LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent
from app.models.media_engine import MediaContent
from app.models.norns_forecast import NornsForecast
from app.models.specialist_assignment import SpecialistAssignment
from app.pantheon.monitor import run_assignment
from app.routers import norns_forecasts


def test_norns_requires_pre_execution_forecast_and_scores_only_observed_outcomes(deal_client, monkeypatch):
    client, engine = deal_client
    factory = {"X-Business-Factory-Key": "fixture-norns-factory"}
    owner = {**factory, "X-Owner-Mandate-Key": "fixture-norns-owner"}
    monkeypatch.setenv("VALHALLA_FACTORY_KEY", factory["X-Business-Factory-Key"])
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", owner["X-Owner-Mandate-Key"])
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    for model in (LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent, MediaContent, NornsForecast, SpecialistAssignment):
        model.__table__.create(engine)
    with Session(engine) as db:
        db.add(LegacyInstanceRegistryItem(
            legacy_instance_id="cal-legacy", display_name="Calibration fixture", synchronization_status="SYNCED",
            assigned_businesses_json='["internal-product"]', assigned_jurisdictions_json='["CA-MB"]',
            local_knowledge_context_json='{"business_id":"internal-product","jurisdiction":"CA-MB"}',
            engines_json='["micro_saas"]', status="PASS",
        ))
        db.commit()

    base = "/api/prime/norns"
    forecasts = f"{base}/forecasts"
    factory_root = "/api/business-factory"
    assert client.get(f"{base}/calibration").json()["brier_score"] is None

    def queue(key):
        listing = client.post(f"{factory_root}/listing-drafts", headers=factory, json={
            "legacy_instance_id": "cal-legacy", "business_id": "internal-product", "jurisdiction": "CA-MB",
            "engine_id": "micro_saas", "industry": "digital goods", "product_id": "calibration-test",
            "title": "Calibration draft fixture", "description": "A private internal draft for measuring resolution timing.",
            "price_cents_cad": 700, "request_key": key,
        })
        assert listing.status_code == 200, listing.text
        return listing.json()["action_id"]

    def forecast(action_id, bp):
        return {"forecast_id": str(uuid4()), "action_id": action_id, "probability_bp": bp, "horizon_seconds": 120}

    action_id = queue("forecast-completion")
    estimate = forecast(action_id, 8000)
    assert client.post(forecasts, json=estimate).status_code == 401
    initial = client.post(forecasts, headers=owner, json=estimate)
    assert initial.status_code == 201, initial.text
    assert initial.json()["estimate_source"] == "OWNER_ESTIMATE"
    assert initial.json()["observed_outcome"] is None
    assert client.post(forecasts, headers=owner, json={**estimate, "forecast_id": str(uuid4())}).status_code == 409
    resolve = f"{forecasts}/{estimate['forecast_id']}/resolve"
    assert client.post(resolve).status_code == 409

    approval = client.post(f"{factory_root}/actions/{action_id}/approve", headers=owner,
                           json={"confirmation": "APPROVE_INTERNAL_DRAFT"})
    assert approval.status_code == 200, approval.text
    result = client.post(f"{factory_root}/actions/run-once", headers=factory)
    assert result.json()["status"] == "completed"
    assert client.post(forecasts, headers=owner, json=forecast(action_id, 3000)).status_code == 409
    observation = client.post(resolve)
    assert observation.status_code == 200, observation.text
    assert observation.json()["observed_outcome"] == 1
    assert observation.json()["evidence_ref"].startswith("BF-RECEIPT-")
    assert client.post(resolve).json() == observation.json()

    pending = forecast(queue("forecast-deadline"), 3000)
    assert client.post(forecasts, headers=owner, json=pending).status_code == 201
    simulated_clock = norns_forecasts._now() + timedelta(minutes=3)
    monkeypatch.setattr(norns_forecasts, "_now", lambda: simulated_clock)
    missed = client.post(f"{forecasts}/{pending['forecast_id']}/resolve")
    assert missed.status_code == 200, missed.text
    assert missed.json()["observed_outcome"] == 0
    assert "NO_RECEIPT" in missed.json()["evidence_ref"]
    stats = client.get(f"{base}/calibration").json()
    assert stats["resolved_sample_count"] == 2
    assert stats["brier_score"] == 0.065
    assert stats["accuracy_claim"] == "OBSERVED_INTERNAL_SAMPLE"

    third = forecast(queue("another-missed-deadline"), 4000)
    assert client.post(forecasts, headers=owner, json=third).status_code == 201
    later = simulated_clock + timedelta(minutes=3)
    monkeypatch.setattr(norns_forecasts, "_now", lambda: later)
    assert client.post(f"{forecasts}/{third['forecast_id']}/resolve").json()["observed_outcome"] == 0
    candidate = queue("prospective-norns-worker")
    assigned = client.post("/api/prime/pantheon/assignments", headers=owner, json={
        "assignment_id": str(uuid4()), "role": "NORNS", "cadence_seconds": 120, "duration_seconds": 1800,
        "legacy_instance_id": "cal-legacy", "business_id": "internal-product", "jurisdiction": "CA-MB",
        "engine_id": "micro_saas",
    })
    assert assigned.status_code == 201, assigned.text
    with Session(engine) as db:
        report_id = run_assignment(db, "NORNS", now=later + timedelta(seconds=1))["report_event_id"]
    report = client.get(f"/api/prime/pantheon/reports/{report_id}").json()["observations"]
    assert report["forecast_status"] == "ISSUED"
    assert report["action_id"] == candidate
    assert report["probability"] == 0.4
    estimate_id = report["forecast_id"]
    prospective = client.get(f"{forecasts}/{estimate_id}").json()
    assert prospective["estimate_source"] == "SCOPED_HISTORICAL_RATE"
    assert set(prospective["training_evidence"]["eligible_forecast_ids"]) == {
        estimate["forecast_id"], pending["forecast_id"], third["forecast_id"],
    }
    assert prospective["observed_outcome"] is None
    query = {"estimate_source": "SCOPED_HISTORICAL_RATE"}
    assert client.get(f"{base}/calibration", params=query).json()["resolved_sample_count"] == 0
    monkeypatch.setattr(norns_forecasts, "_now", lambda: later + timedelta(minutes=3))
    assert client.post(f"{forecasts}/{estimate_id}/resolve").json()["observed_outcome"] == 0
    assert client.get(f"{base}/calibration", params=query).json()["brier_score"] == 0.16
    assert client.get(f"{base}/calibration").json()["resolved_sample_count"] == 3
