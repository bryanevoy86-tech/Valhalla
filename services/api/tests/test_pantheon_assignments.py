import json
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.completion_registry import LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent
from app.models.media_engine import MediaContent
from app.models.specialist_assignment import SpecialistAssignment
from app.pantheon.monitor import run_assignment, utc_now
from app.pantheon.roles import ROLES
from app.services.owner_operating_brief import operating_evidence


def test_workers_run_independent_role_and_scope_cadences_and_recheck_factory_outcomes(deal_client, monkeypatch):
    client, engine = deal_client
    factory = {"X-Business-Factory-Key": "active-intel-factory-fixture"}
    owner = {**factory, "X-Owner-Mandate-Key": "active-intel-owner-fixture"}
    monkeypatch.setenv("VALHALLA_FACTORY_KEY", factory["X-Business-Factory-Key"])
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", owner["X-Owner-Mandate-Key"])
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    for model in (LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent, MediaContent, SpecialistAssignment):
        model.__table__.create(engine)
    scopes = [
        {"legacy_instance_id": "research-legacy", "business_id": "research-lab", "jurisdiction": "CA-MB", "engine_id": "micro_saas"},
        {"legacy_instance_id": "another-legacy", "business_id": "another-lab", "jurisdiction": "CA-ON", "engine_id": "micro_saas"},
    ]
    with Session(engine) as db:
        for scope in scopes:
            db.add(LegacyInstanceRegistryItem(
                legacy_instance_id=scope["legacy_instance_id"], display_name=scope["legacy_instance_id"],
                synchronization_status="SYNCED", status="PASS", engines_json='["micro_saas"]',
                assigned_businesses_json=json.dumps([scope["business_id"]]),
                assigned_jurisdictions_json=json.dumps([scope["jurisdiction"]]),
                local_knowledge_context_json=json.dumps(scope),
            ))
        db.commit()

    root = "/api/prime/pantheon"
    assert set(client.get(f"{root}/roles").json()["local_monitoring_lenses"]) == set(ROLES)

    def assign(scope, role):
        request = {**scope, "role": role, "assignment_id": str(uuid4()), "cadence_seconds": 600, "duration_seconds": 1800}
        assert client.post(f"{root}/assignments", json=request).status_code == 401
        enrolled = client.post(f"{root}/assignments", json=request, headers=owner)
        assert enrolled.status_code == 201, enrolled.text
        return request["assignment_id"]

    correct = assign(scopes[0], "MIMIR")
    other = assign(scopes[1], "MIMIR")
    tyr = assign(scopes[0], "TYR")
    at = utc_now() + timedelta(seconds=1)

    def tick(role):
        with Session(engine) as db:
            result = run_assignment(db, role, now=at)
        if result["status"] in {"idle", "blocked"} and not result.get("report_event_id"):
            return result
        response = client.get(f"{root}/reports/{result['report_event_id']}")
        assert response.status_code == 200, response.text
        return response.json()

    assert tick("ODIN") == {"status": "idle"}
    assert {tick("MIMIR")["assignment_id"], tick("MIMIR")["assignment_id"]} == {correct, other}
    initial = tick("TYR")
    assert initial["assignment_id"] == tyr
    assert initial["observations"]["recorded_approval_event_ids"] == []
    assert tick("MIMIR") == {"status": "idle"}
    previous = client.get(f"{root}/assignments/{other}").json()

    factory_root = "/api/business-factory"
    assignment = client.post(f"{factory_root}/listing-drafts", headers=factory, json={
        **scopes[0], "industry": "digital goods", "product_id": "specialist-fixture",
        "title": "Assignment verification fixture", "description": "This local draft triggers an evidence-based assignment.",
        "price_cents_cad": 500, "request_key": "specialist-trigger-draft",
    })
    assert assignment.status_code == 200, assignment.text
    action = assignment.json()["action_id"]
    approval = client.post(f"{factory_root}/actions/{action}/approve", headers=owner, json={
        "confirmation": "APPROVE_INTERNAL_DRAFT",
    })
    assert approval.status_code == 200, approval.text
    outcome = client.post(f"{factory_root}/actions/run-once", headers=factory).json()
    assert outcome["status"] == "completed"

    report = tick("MIMIR")
    assert report["assignment_id"] == correct
    assert report["trigger"] == "VERIFIED_OUTCOME"
    assert report["trigger_event_id"] in report["observations"]["verified_internal_outcomes"]
    assert report["external_authority"] is False
    assert tick("MIMIR") == {"status": "idle"}
    with Session(engine) as db:
        resumed = db.get(SpecialistAssignment, UUID(correct))
        due_at = resumed.next_due_at
        resumed.pending_event_id = report["trigger_event_id"]
        db.commit()
        # A duplicate wake-up and the missed cadence coexist after an interruption.
        recovered_at = due_at + timedelta(seconds=610)
        assert run_assignment(db, "MIMIR", now=recovered_at) == {
            "status": "replayed", "report_event_id": report["report_event_id"],
        }
        assert resumed.next_due_at == due_at
    with Session(engine) as db:
        resumed_reports = [run_assignment(db, "MIMIR", now=recovered_at) for _ in range(2)]
        assert all(result["status"] == "observed" for result in resumed_reports)
        assert run_assignment(db, "MIMIR", now=recovered_at) == {"status": "idle"}
        alerts = operating_evidence(db)["specialist_cadence_alerts"]
        assert any(alert["scope"] == scopes[0] and alert["missed_slots"] == 1 for alert in alerts)
    resumed_reports = [client.get(f"{root}/reports/{item['report_event_id']}").json() for item in resumed_reports]
    recovered_report = next(item for item in resumed_reports if item["assignment_id"] == correct)
    assert recovered_report["trigger"] == "CADENCE"
    assert recovered_report["cadence"]["slots_elapsed"] == 2
    assert recovered_report["cadence"]["missed_slots"] == 1
    assert client.get(f"{root}/assignments/{other}").json()["scope"] == previous["scope"]
    assert tick("TYR")["observations"]["recorded_approval_event_ids"] == [f"BF-APPROVED-{action}"]

    with Session(engine) as db:
        saved = db.query(LegacyOrchestrationEvent).filter_by(event_id=report["report_event_id"]).one()
        saved.payload_json = saved.payload_json.replace("VERIFIED_OUTCOME", "UNVERIFIED")
        db.get(SpecialistAssignment, UUID(correct)).pending_event_id = report["trigger_event_id"]
        db.commit()
        with pytest.raises(HTTPException) as rejected:
            run_assignment(db, "MIMIR", now=at)
        assert rejected.value.status_code == 409
    assert client.get(f"{root}/reports/{report['report_event_id']}").status_code == 409
    assert client.delete(f"{root}/assignments/{correct}", headers=owner).json()["state"] == "revoked"
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    assert tick("MIMIR") == {"status": "blocked", "emergency_stop": True}
