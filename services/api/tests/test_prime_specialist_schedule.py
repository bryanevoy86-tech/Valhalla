from datetime import timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.completion_registry import (
    KnowledgeRegistryItem, LearningFeedbackRecord, LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent,
)
from app.models.media_engine import MediaContent
from app.models.prime_specialist_schedule import PrimeSpecialistSchedule
from app.routers.prime_specialist_schedules import REPORT_EVENT, _utc_now, run_due_schedule


ROOT = "/api/prime/specialist-schedules"


def test_owner_schedule_runs_durable_scoped_shadow_advice(deal_client, monkeypatch):
    client, engine = deal_client
    owner = {"X-Owner-Mandate-Key": "ci-owner-mandate-specialist"}
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", owner["X-Owner-Mandate-Key"])
    schedule_id = str(uuid4())
    config = {
        "schedule_id": schedule_id, "business_id": "internal-product", "cadence_seconds": 300,
        "duration_seconds": 1800,
        "opportunity": {
            "opportunity_id": "scheduler-01", "engine_id": "micro_saas", "legacy": "legacy-01",
            "jurisdiction": "CA-MB", "title": "Product opportunity", "summary": "Internal hypotheses and evidence.",
        },
    }
    for model in (
        KnowledgeRegistryItem, LearningFeedbackRecord, LegacyInstanceRegistryItem, LegacyInstanceWorkItem,
        LegacyOrchestrationEvent, MediaContent,
    ):
        model.__table__.create(engine)
    assert client.post(ROOT, headers=owner, json=config).status_code == 503
    PrimeSpecialistSchedule.__table__.create(engine)
    assert client.post(ROOT, json=config).status_code == 401
    assert client.post(ROOT, headers=owner, json=config).status_code == 409

    with Session(engine) as db:
        db.add(LegacyInstanceRegistryItem(
            legacy_instance_id="legacy-01", display_name="Internal Legacy",
            assigned_businesses_json='["internal-product"]', assigned_jurisdictions_json='["CA-MB"]',
            local_knowledge_context_json='{"business_id":"internal-product","jurisdiction":"CA-MB"}',
            engines_json='["micro_saas"]', synchronization_status="SYNCED", status="PASS",
        ))
        db.commit()

    created = client.post(ROOT, headers=owner, json=config)
    assert created.status_code == 201, created.text
    assert client.post(ROOT, headers=owner, json=config).json() == created.json()
    assert client.post(ROOT, headers=owner, json={**config, "cadence_seconds": 600}).status_code == 409
    assert client.get(f"{ROOT}/{schedule_id}", headers={"X-Prime-Control-Key": "wrong"}).status_code == 401

    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    with Session(engine) as db:
        assert run_due_schedule(db) == {"status": "blocked", "emergency_stop": True}
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    tick_time = _utc_now() + timedelta(seconds=605)
    with Session(engine) as db:
        tick = run_due_schedule(db, now=tick_time)
        assert tick["status"] == "evaluated"
    with Session(engine) as db:
        assert run_due_schedule(db, now=tick_time) == {"status": "idle"}
        assert db.query(LegacyOrchestrationEvent).filter_by(event_type=REPORT_EVENT).count() == 1
        assert db.query(LegacyInstanceWorkItem).count() == 0
        assert db.query(LearningFeedbackRecord).count() == 0

    report = client.get(f"{ROOT}/{schedule_id}").json()["latest_report"]
    assert report["report_event_id"] == tick["report_event_id"]
    assert report["evaluation"]["opportunity_id"] == "scheduler-01"
    assert report["evaluation"]["persistence"] is None
    assert report["effect"] == "ADVISORY_ONLY"
    assert report["external_authority"] is False
    assert report["independent_loki_cleared"] is False
    assert report["missed_slots_coalesced"] == 2
    assert report["verified_internal_outcomes"] == []

    with Session(engine) as db:
        db.query(LegacyInstanceRegistryItem).one().synchronization_status = "STALE"
        db.commit()
    with Session(engine) as db:
        assert run_due_schedule(db, now=tick_time + timedelta(seconds=300))["status"] == "blocked"
    report = client.get(f"{ROOT}/{schedule_id}").json()["latest_report"]
    assert "policy sync" in report["reason"]
    assert "evaluation" not in report
    prior = client.get(f"{ROOT}/{schedule_id}/reports/{tick['report_event_id']}")
    assert prior.json()["status"] == "evaluated"
    assert client.get(f"{ROOT}/{uuid4()}/reports/{tick['report_event_id']}").status_code == 404

    assert client.delete(f"{ROOT}/{schedule_id}").status_code == 401
    assert client.delete(f"{ROOT}/{schedule_id}", headers=owner).json()["state"] == "cancelled"
    with Session(engine) as db:
        assert run_due_schedule(db, now=tick_time + timedelta(seconds=600)) == {"status": "idle"}
