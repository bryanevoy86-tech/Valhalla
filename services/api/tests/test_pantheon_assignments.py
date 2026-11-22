import json
from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.completion_registry import (
    KnowledgeRegistryItem, LearningFeedbackRecord, LegacyInstanceRegistryItem, LegacyInstanceWorkItem,
    LegacyOrchestrationEvent,
)
from app.models.prime_specialist_schedule import PrimeScheduleTrigger, PrimeSpecialistSchedule
from app.routers.prime_specialist_schedules import run_due_schedule
from app.services.prime_business_execution import _approval_id, _mimir_outcome_id
from app.models.media_engine import MediaContent
from app.models.specialist_assignment import SpecialistAssignment, SpecialistTrigger
from app.pantheon.monitor import run_assignment, utc_now
from app.pantheon.roles import ROLES
from app.services.owner_operating_brief import operating_evidence
from app.services.specialist_triggers import enqueue_research, outcome_scope_key


def test_workers_run_independent_role_and_scope_cadences_and_recheck_factory_outcomes(deal_client, monkeypatch):
    client, engine = deal_client
    factory = {"X-Business-Factory-Key": "active-intel-factory-fixture"}
    owner = {**factory, "X-Owner-Mandate-Key": "active-intel-owner-fixture"}
    monkeypatch.setenv("VALHALLA_FACTORY_KEY", factory["X-Business-Factory-Key"])
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", owner["X-Owner-Mandate-Key"])
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    for model in (LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent, MediaContent, SpecialistAssignment,
                  SpecialistTrigger, PrimeSpecialistSchedule, PrimeScheduleTrigger, KnowledgeRegistryItem,
                  LearningFeedbackRecord):
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

    schedules = "/api/prime/specialist-schedules"
    schedule_id = str(uuid4())
    registered = client.post(schedules, headers=owner, json={
        "schedule_id": schedule_id, "business_id": scopes[0]["business_id"],
        "cadence_seconds": 300, "duration_seconds": 1800,
        "opportunity": {
            "opportunity_id": "factory-evidence-rehearsal", "engine_id": scopes[0]["engine_id"],
            "legacy": scopes[0]["legacy_instance_id"], "jurisdiction": scopes[0]["jurisdiction"],
            "title": "Factory evidence rehearsal", "summary": "Internal workflow evidence only.",
        },
    })
    assert registered.status_code == 201, registered.text

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
        for invalid in ("DISCOVERY-duplicate-source", "ECON-missing-financial-evidence"):
            enqueue_research(db, outcome_scope_key(scopes[0]), invalid, at, roles={"MIMIR"})
        enqueue_research(db, outcome_scope_key(scopes[0]), report["trigger_event_id"],
                         at - timedelta(seconds=1), roles={"MIMIR"})
        enqueue_research(db, outcome_scope_key(scopes[0]), report["trigger_event_id"],
                         at, roles={"MIMIR"})
        db.commit()
        assert client.get(f"{root}/assignments/{correct}").json()["queued_event_count"] == 3
        assert client.get(f"{root}/assignments/{other}").json()["queued_event_count"] == 0
        monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
        assert run_assignment(db, "MIMIR", now=at)["status"] == "blocked"
        monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
        # A duplicate wake-up and the missed cadence coexist after an interruption.
        recovered_at = due_at + timedelta(seconds=610)
        assert run_assignment(db, "MIMIR", now=recovered_at) == {
            "status": "replayed", "report_event_id": report["report_event_id"],
        }
        assert resumed.next_due_at == due_at
        blocked = [run_assignment(db, "MIMIR", now=at) for _ in range(2)]
        assert [result["status"] for result in blocked] == ["blocked", "blocked"]
        assert {client.get(f"{root}/reports/{item['report_event_id']}").json()["trigger"] for item in blocked} == {
            "SOURCE_DISCOVERY", "ECONOMIC_REASSESSMENT",
        }
        assert run_assignment(db, "MIMIR", now=at) == {"status": "idle"}
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
        enqueue_research(db, outcome_scope_key(scopes[0]), report["trigger_event_id"], at, roles={"MIMIR"})
        db.commit()
        assert run_assignment(db, "MIMIR", now=at) == {
            "status": "blocked", "failure_code": "EXISTING_REPORT_INTEGRITY_FAILED",
        }
        assert run_assignment(db, "MIMIR", now=at) == {"status": "idle"}
        assert operating_evidence(db)["specialist_queue"]["pantheon"]["failed"] == 1
        assert client.get(f"{root}/assignments/{correct}").json()["failed_event_counts"] == {
            "EXISTING_REPORT_INTEGRITY_FAILED": 1,
        }
    assert client.get(f"{root}/reports/{report['report_event_id']}").status_code == 409
    def tick_prime(when):
        with Session(engine) as db:
            result = run_due_schedule(db, now=when)
        assert result["status"] == "evaluated", result
        response = client.get(f"{schedules}/{schedule_id}/reports/{result['report_event_id']}")
        assert response.status_code == 200, response.text
        return response.json()

    baseline = tick_prime(at)
    assert "factory_evidence_contradictions" not in (baseline.get("operating_reassessment") or {})
    approval_id, outcome_id = _approval_id(action), _mimir_outcome_id(action)
    with Session(engine) as db:
        receipts = db.query(LegacyOrchestrationEvent).filter(
            LegacyOrchestrationEvent.event_id.in_([approval_id, outcome_id]),
        ).all()
        originals = {row.event_id: row.payload_json for row in receipts}
        assert set(originals) == {approval_id, outcome_id}
        for row in receipts:
            row.payload_json = "{}"
        db.commit()
    conflicted_at = at + timedelta(seconds=601)
    conflict = tick_prime(conflicted_at)
    reassessment = conflict["operating_reassessment"]
    expected = {"FACTORY_APPROVAL_BINDING_MISMATCH", "MIMIR_OUTCOME_UNVERIFIED"}
    assert set(reassessment["blockers"]) == expected
    assert {item["evidence_ref"] for item in reassessment["factory_evidence_contradictions"]} == {
        approval_id, outcome_id,
    }
    assert conflict["recommendation"]["heimdall_decision"] == "HOLD"
    assert conflict["verified_internal_outcomes"] == []
    with Session(engine) as db:
        tyr_result = run_assignment(db, "TYR", now=conflicted_at)
    findings = client.get(f"{root}/reports/{tyr_result['report_event_id']}").json()["observations"][
        "factory_evidence_reconciliation"
    ]
    assert findings["verified_approval_event_ids"] == []
    assert {item["code"] for item in findings["contradictions"]} == expected
    with Session(engine) as db:
        for row in db.query(LegacyOrchestrationEvent).filter(LegacyOrchestrationEvent.event_id.in_(originals)):
            row.payload_json = originals[row.event_id]
        db.commit()
    reconciled = tick_prime(at + timedelta(seconds=902))
    assert "factory_evidence_contradictions" not in (reconciled.get("operating_reassessment") or {})
    assert len(reconciled["verified_internal_outcomes"]) == 1
    assert client.delete(f"{root}/assignments/{correct}", headers=owner).json()["state"] == "revoked"
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    assert tick("MIMIR") == {"status": "blocked", "emergency_stop": True}


def test_queued_mimir_outcome_older_than_recent_window_reaches_prime(deal_client, monkeypatch):
    from app.services.prime_business_execution import verified_internal_outcomes
    from app.services.specialist_triggers import publish_verified_outcome

    client, engine = deal_client
    owner = {"X-Owner-Mandate-Key": "older-outcome-owner", "X-Business-Factory-Key": "older-outcome-factory"}
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", owner["X-Owner-Mandate-Key"])
    monkeypatch.setenv("VALHALLA_FACTORY_KEY", owner["X-Business-Factory-Key"])
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    for model in (LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent, MediaContent,
                  SpecialistAssignment, SpecialistTrigger, PrimeSpecialistSchedule, PrimeScheduleTrigger,
                  KnowledgeRegistryItem, LearningFeedbackRecord):
        model.__table__.create(engine)
    scope = {"legacy_instance_id": "archive-legacy", "business_id": "archive-lab",
             "jurisdiction": "CA-MB", "engine_id": "micro_saas"}
    with Session(engine) as db:
        db.add(LegacyInstanceRegistryItem(
            legacy_instance_id="archive-legacy", display_name="Artifact archive", status="PASS",
            synchronization_status="SYNCED", engines_json='["micro_saas"]',
            assigned_businesses_json='["archive-lab"]', assigned_jurisdictions_json='["CA-MB"]',
            local_knowledge_context_json=json.dumps(scope),
        ))
        db.commit()

    factory = "/api/business-factory"
    actions = []
    for index in range(21):
        queued = client.post(f"{factory}/listing-drafts", headers=owner, json={
            **scope, "industry": "digital goods", "product_id": "archive-fixture",
            "title": "Historical internal draft", "description": "A scoped internal fixture used to verify delayed outcome consumption.",
            "price_cents_cad": 500, "request_key": f"historical-outcome-{index}",
        })
        assert queued.status_code == 200, queued.text
        action = queued.json()["action_id"]
        assert client.post(f"{factory}/actions/{action}/approve", headers=owner,
                           json={"confirmation": "APPROVE_INTERNAL_DRAFT"}).status_code == 200
        executed = client.post(f"{factory}/actions/run-once", headers=owner)
        assert executed.json()["status"] == "completed"
        actions.append(action)

    old_event = _mimir_outcome_id(actions[0])
    schedule_id = str(uuid4())
    schedules = "/api/prime/specialist-schedules"
    assert client.post(schedules, headers=owner, json={
        "schedule_id": schedule_id, "business_id": scope["business_id"],
        "cadence_seconds": 300, "duration_seconds": 1800, "on_verified_outcome": True,
        "opportunity": {"opportunity_id": "historical-proof", "engine_id": scope["engine_id"],
                        "legacy": scope["legacy_instance_id"], "jurisdiction": scope["jurisdiction"],
                        "title": "Historical proof review", "summary": "Verified internal evidence."},
    }).status_code == 201
    pantheon = "/api/prime/pantheon"
    assert client.post(f"{pantheon}/assignments", headers=owner, json={
        **scope, "assignment_id": str(uuid4()), "role": "MIMIR",
        "cadence_seconds": 300, "duration_seconds": 1800,
    }).status_code == 201

    at = utc_now() + timedelta(seconds=2)
    with Session(engine) as db:
        assert old_event not in {row["outcome_event_id"] for row in verified_internal_outcomes(db, **scope)}
        foreign = {**scope, "jurisdiction": "CA-ON"}
        assert verified_internal_outcomes(db, **foreign, trigger_event_id=old_event) == []
        publish_verified_outcome(db, scope, old_event)
        db.commit()
        prime = run_due_schedule(db, now=at)
        mimir = run_assignment(db, "MIMIR", now=at)
        assert prime["status"] == "evaluated"
        assert mimir["status"] == "observed"
    report = client.get(f"{schedules}/{schedule_id}/reports/{prime['report_event_id']}").json()
    assert report["trigger_outcome_event_id"] == old_event
    assert report["verified_internal_outcomes"][0]["outcome_event_id"] == old_event
    assert len(report["verified_internal_outcomes"]) == 21
    observation = client.get(f"{pantheon}/reports/{mimir['report_event_id']}").json()
    assert old_event in observation["observations"]["verified_internal_outcomes"]
