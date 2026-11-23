from datetime import datetime, timedelta, timezone
import json
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.auth_revocations import RevokedAccessToken
from app.models.audit_log import AuditLog
from app.models.completion_registry import LearningTaskQueueItem, LegacyOrchestrationEvent
from app.models.go_live_state import GoLiveState
from app.models.prime_specialist_schedule import PrimeScheduleTrigger, PrimeSpecialistSchedule
from app.models.saas_access import SaaSPlan, SaaSPlanModule, SaaSTenantEntitlement, Subscription
from app.routers.auth_weweb import _auth_runtime, _issue_access_token
from app.users.models import AccountSettings, UserProfile


def test_trial_is_bound_to_authenticated_subscriber_and_tenant(deal_client, monkeypatch):
    client, engine = deal_client
    key = "internal-saas-test-owner"
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", key)
    owner = {"X-Owner-Mandate-Key": key}
    for model in (SaaSPlan, SaaSPlanModule, Subscription, UserProfile, AccountSettings, RevokedAccessToken, SaaSTenantEntitlement):
        model.__table__.create(engine)

    with Session(engine) as db:
        profiles = [UserProfile(first_name="Test", last_name=label, email=f"{label}@example.invalid") for label in ("one", "two")]
        db.add_all(profiles)
        db.flush()
        for profile in profiles:
            db.add(AccountSettings(user_id=profile.user_id, account_locked=False, password_hash="unused-fixture"))
        db.commit()
        subject_id = profiles[0].user_id
        runtime = _auth_runtime()
        bearer, outsider = ({"Authorization": f"Bearer {_issue_access_token(runtime, profile)}"} for profile in profiles)

    data = {"code": "TRIAL", "name": "Internal trial", "modules": [{"module_key": "wholesale_engine"}]}
    assert client.post("/saas/plans", json=data).status_code == 401
    plan = client.post("/saas/plans", headers=owner, json=data)
    assert plan.status_code == 200, plan.text
    assert client.post("/saas/subscriptions", json={"user_id": subject_id, "plan_id": plan.json()["id"]}).status_code == 401

    fake = {"user_id": subject_id, "plan_id": plan.json()["id"], "provider": "stripe",
            "provider_sub_id": " PI_FIXTURE_refunded_order "}
    assert client.post("/saas/subscriptions", headers=owner, json=fake).status_code == 409
    # Previously persisted fixture IDs must remain visible for review without granting access.
    with Session(engine) as db:
        contaminated = Subscription(**fake)
        db.add(contaminated)
        db.commit()
        contaminated_id = contaminated.id
    check = client.get("/saas/access-check", params={"user_id": subject_id, "module_key": "wholesale_engine"})
    assert check.status_code == 200 and check.json()["has_access"] is False
    assert client.patch(f"/saas/subscriptions/{contaminated_id}", headers=owner,
                        json={"status": "active"}).status_code == 409
    assert client.patch(f"/saas/subscriptions/{contaminated_id}", headers=owner,
                        json={"status": "cancelled"}).status_code == 200
    assert client.patch(f"/saas/subscriptions/{contaminated_id}", headers=owner,
                        json={"provider_sub_id": None}).status_code == 409
    unverified = {**fake, "provider_sub_id": "sub_unverified_fixture_test"}
    pending_subscription = client.post("/saas/subscriptions", headers=owner, json=unverified)
    assert pending_subscription.status_code == 200 and pending_subscription.json()["status"] == "pending_verification"
    subscription_path = f"/saas/subscriptions/{pending_subscription.json()['id']}"
    assert client.patch(subscription_path, headers=owner, json={"status": "active"}).status_code == 409
    with Session(engine) as db:
        db.get(Subscription, pending_subscription.json()["id"]).status = "active"
        db.commit()
    assert client.get("/saas/access-check", params={
        "user_id": subject_id, "module_key": "wholesale_engine",
    }).json()["has_access"] is False
    assert client.patch(subscription_path, headers=owner, json={"status": "cancelled"}).status_code == 200

    trial = {
        "entitlement_id": str(uuid4()), "tenant_id": str(uuid4()), "subject_id": subject_id, "plan_id": plan.json()["id"],
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(), "modules": ["wholesale_engine"],
    }
    root = "/saas/tenant-entitlements"
    invalid_module = client.post(root, headers=owner, json={**trial, "modules": ["heimdall_prime"]})
    assert invalid_module.status_code == 422
    issued = client.post(root, headers=owner, json=trial)
    assert issued.status_code == 201, issued.text
    assert issued.json()["payment_verified"] is False
    assert client.post(root, headers=owner, json=trial).json() == issued.json()

    monkeypatch.setenv("VALHALLA_OWNER_EMAIL", "one@example.invalid")
    from app.services import owner_startup

    monkeypatch.setattr(owner_startup, "FEE_CHECKED_ON", datetime.now(timezone.utc).date())
    path = "/api/weweb/owner-startup/compare"
    plan = {
        "named_corporation": True, "manitoba_operations": True, "startup_cash_available_minor": 50000,
        "operating_reserve_target_minor": 120000, "operating_cash_available_minor": 60000,
        "funded_infrastructure": [{"key": "fixture-host", "label": "Existing host",
                                    "funded_to_date_minor": 40000, "committed_monthly_minor": 2000}],
        "surplus_assets": [{"label": "Hypothetical excess fixture", "owner_valuation_minor": 800000}],
        "costs": [
            {"key": "corporate_legal", "label": "Fixture legal quote", "cadence": "ACTIVATION",
             "basis": "PROFESSIONAL_QUOTE", "amount_minor": 20000, "reference": "private-fixture-quote"},
            {"key": "tax_and_accounting", "label": "Fixture accountant", "cadence": "ACTIVATION",
             "basis": "PROFESSIONAL_QUOTE", "amount_minor": 10000, "reference": "private-fixture-accountant"},
            {"key": "commission", "label": "Incremental maintenance", "cadence": "MONTHLY",
             "basis": "OWNER_ESTIMATE", "amount_minor": 3000},
        ],
    }
    plan["professional_review"] = [{
        "route": "INTERNATIONAL_FIRST", "topic": "TAX_RESIDENCY",
        "facts": [{"label": "Proposed decision location", "statement": "Management would initially work in Manitoba.",
                   "source_reference": "owner:startup-fixture", "observed_on": datetime.now(timezone.utc).date().isoformat()}],
        "questions": ["What residency and reporting questions require independent review?"],
    }]
    assert client.post(path, json=plan).status_code == 401
    assert client.post(path, headers=outsider, json=plan).status_code == 403
    opinions = "/tax-bridge/opinions"
    opinion_id = str(uuid4())
    wrong_prime = {"X-Prime-Control-Key": "wrong"}
    assert client.get(f"{opinions}/{opinion_id}", headers=wrong_prime).status_code == 401
    assert client.get(f"{opinions}/{opinion_id}").status_code == 503
    quote = client.post(path, headers=bearer, json=plan)
    assert quote.status_code == 200, quote.text
    assert quote.headers["cache-control"] == "no-store"
    dependency_path = "/api/weweb/owner-startup/dependencies"
    assert client.get(dependency_path).status_code == 401
    assert client.get(dependency_path, headers=outsider).status_code == 403
    dependencies = client.get(dependency_path, headers=bearer)
    assert dependencies.status_code == 200 and dependencies.headers["cache-control"] == "no-store"
    plan_only = dependencies.json()
    assert quote.json()["startup_dependencies"] == plan_only
    gates = {item["key"]: item["gate"] for item in plan_only["dependencies"]}
    assert gates["registration"] == "REGISTRATION" and gates["bank"] == "FIRST_REVENUE"
    assert gates["expansion"] == gates["recurring_settlement"] == "LATER"
    recurring = client.get(dependency_path, headers=bearer, params={"lane": "RECURRING_CAD"}).json()
    assert next(item for item in recurring["dependencies"] if item["key"] == "recurring_settlement")["gate"] == "FIRST_REVENUE"
    invalid_lane = client.get(dependency_path, headers=bearer, params={"lane": "secret-fixture"})
    assert invalid_lane.status_code == 422 and "secret-fixture" not in invalid_lane.text
    review_path = "/api/weweb/owner-startup/independence-review"
    review_payload = {
        "monthly_essentials_minor": 100000, "reserve_months": 3, "reserve_balance_minor": 0,
        "monthly_stretch_low_minor": 120000, "monthly_stretch_high_minor": 160000,
        "opening_unrestricted_cash_fixture_minor": 50000, "establishment_minor": 42000,
        "operating_minor": 15000, "business_reserve_minor": 8000, "experiment_minor": 2000,
        "reporting_month": datetime.now(timezone.utc).date().replace(day=1).isoformat(),
    }
    assert client.post(review_path, json=review_payload).status_code == 401
    assert client.post(review_path, headers=outsider, json=review_payload).status_code == 403
    independence = client.post(review_path, headers=bearer, json=review_payload)
    assert independence.status_code == 200, independence.text
    assert independence.headers["cache-control"] == "no-store"
    assert independence.json()["external_action_authorized"] is False
    private_marker = "private-fixture-should-not-echo"
    invalid = client.post(review_path, headers=bearer, json={**review_payload, "reserve_months": private_marker})
    assert invalid.status_code == 422 and invalid.headers["cache-control"] == "no-store"
    assert private_marker not in invalid.text
    denied = client.post(review_path, headers=outsider, json=review_payload)
    assert denied.headers["cache-control"] == "no-store"
    budget = quote.json()
    [packet] = budget["professional_review_packets"]
    assert packet["jurisdiction"] == "Panama"
    assert packet["facts"][0]["basis"] == "OWNER_REPORTED"
    assert packet["status"] == "DRAFT_AWAITING_QUALIFIED_REVIEW"
    assert packet["professional_signoff"] is None and packet["reliance_authorized"] is False
    review = plan["professional_review"][0]
    assert client.post(path, headers=bearer, json={**plan, "professional_review": [review, review]}).status_code == 422
    assert client.post(path, headers=bearer, json={
        **plan, "professional_review": [{**review, "professional_signoff": "unverified owner claim"}],
    }).status_code == 422
    mb, federal, foreign = budget["options"]
    assert mb["activation"]["verified_government_minor"] == 39500
    assert mb["activation"]["estimate_including_all_items_minor"] == 69500
    assert mb["activation"]["minimum_additional_capital_minor"] == 19500
    assert federal["activation"]["verified_government_minor"] == 59500
    assert "foreign_filing_cad" in foreign["activation"]["unpriced_keys"]
    assert foreign["activation"]["minimum_additional_capital_minor"] is None
    assert mb["operating"]["known_annual_cost_minor"] == 66500
    assert mb["operating"]["reserve_gap_minor"] == 60000
    assert budget["checklist"][-1]["sequence"] == 7 and budget["selected_jurisdiction"] is None
    assert budget["activation_authorized"] is False and budget["external_effects"] == 0
    assert client.post(path, headers=bearer, json={
        **plan, "costs": [*plan["costs"], {**plan["costs"][0], "key": "fixture-host"}],
    }).status_code == 422
    monkeypatch.setattr(owner_startup, "FEE_CHECKED_ON", datetime.now(timezone.utc).date() - timedelta(days=91))
    stale = client.post(path, headers=bearer, json=plan).json()["options"][0]["activation"]
    assert stale["verified_government_minor"] == 0 and stale["minimum_additional_capital_minor"] is None

    from app.models.owner_conversation import OwnerAttachment, OwnerAttachmentExtraction, OwnerAttachmentReview, OwnerConversation, OwnerTurn

    from app.routers.prime_specialist_schedules import REPORT_EVENT, shadow_report_digest

    for model in (LearningTaskQueueItem, LegacyOrchestrationEvent, GoLiveState, PrimeSpecialistSchedule,
                  PrimeScheduleTrigger, OwnerConversation, OwnerTurn, OwnerAttachment, OwnerAttachmentExtraction, OwnerAttachmentReview):
        model.__table__.create(engine)
    thread_id = uuid4()
    schedule_id, report_id = uuid4(), "PRIME-owner-fixture"
    instant = datetime.now(timezone.utc).replace(tzinfo=None)
    advisory = {
        "schedule_id": str(schedule_id), "report_event_id": report_id, "status": "blocked",
        "scope": {"legacy_instance_id": "test-legacy"}, "trigger": "FOUNDRY_SOURCE_WITHDRAWN",
        "reason": "Private source details", "observed_at": instant.isoformat(),
    }
    advisory["report_sha256"] = shadow_report_digest(report_id, advisory)
    with Session(engine) as db:
        db.add(PrimeSpecialistSchedule(id=schedule_id, request={}, state="active", cadence_seconds=300,
                                     next_due_at=instant, expires_at=instant + timedelta(hours=1),
                                     last_report_event_id=report_id))
        db.add(LegacyOrchestrationEvent(event_id=report_id, legacy_instance_id="test-legacy",
                                        event_type=REPORT_EVENT, message="Private test receipt",
                                        payload_json=json.dumps(advisory)))
        db.add(OwnerConversation(id=thread_id, title="Private fixture conversation"))
        db.add(OwnerTurn(id=uuid4(), conversation_id=thread_id, message="What is blocked?",
                         reply="The simulation is waiting for review.", evidence={"source": "fixture"}, attachment_ids=[]))
        db.add(GoLiveState(id=1, go_live_enabled=False, kill_switch_engaged=True))
        db.commit()
    briefing = "/api/weweb/owner-briefing"
    assert client.get(briefing).status_code == 401
    assert client.get(briefing, headers=outsider).status_code == 403
    owned = client.get(briefing, headers={**bearer, "X-Prime-Control-Key": "not-used"})
    assert owned.status_code == 200, owned.text
    assert owned.headers["cache-control"] == "no-store"
    assert owned.json()["execution_authorized"] is False
    assert owned.json()["evidence"]["integrity"]["fail_safe_state"]["active"] is True
    [prime_alert] = owned.json()["evidence"]["operating_evidence"]["latest_prime_advisory_alerts"]
    assert prime_alert["report_event_id"] == report_id and prime_alert["execution_authorized"] is False
    with Session(engine) as db:
        item = AuditLog(event_type="integrity_alert", event_source="fixture-check", message="Private evidence details")
        db.add(item)
        db.commit()
        alert_id = item.id
    attention = "/api/weweb/owner-attention"
    assert client.get(attention).status_code == 401
    assert client.get(attention, headers=outsider).status_code == 403
    notice = client.get(attention, headers=bearer)
    assert notice.status_code == 200 and notice.headers["cache-control"] == "no-store"
    assert notice.json()["entries"] == [{"notification_id": f"integrity:{alert_id}", "category": "integrity",
                                         "reference": str(alert_id)},
                                        {"notification_id": f"prime_advisory:{report_id}", "category": "prime_advisory",
                                         "reference": report_id}]
    assert notice.json()["delivery_attempted"] is False
    assert "Private evidence details" not in notice.text
    assert client.get(attention, headers=bearer).json() == notice.json()
    assert notice.json()["acknowledged_ids"] == []
    acknowledge = f"{attention}/acknowledge"
    item_id = f"prime_advisory:{report_id}"
    assert client.post(acknowledge, headers=outsider, json={"notification_id": item_id}).status_code == 403
    assert client.post(acknowledge, headers=bearer, json={"notification_id": "review:missing"}).status_code == 404
    ack = client.post(acknowledge, headers=bearer, json={"notification_id": item_id})
    assert ack.status_code == 200 and ack.headers["cache-control"] == "no-store"
    assert ack.json()["acknowledged"] and ack.json()["delivery_attempted"] is False
    assert client.post(acknowledge, headers=bearer, json={"notification_id": item_id}).json() == ack.json()
    assert client.get(attention, headers=bearer).json()["acknowledged_ids"] == [item_id]
    with Session(engine) as db:
        receipt = db.query(LegacyOrchestrationEvent).filter_by(event_type="OWNER_ATTENTION_ACKNOWLEDGED").one()
        assert item_id in receipt.payload_json and "Private source details" not in receipt.payload_json
    driving = client.get(briefing, params={"mode": "driving"}, headers=bearer)
    assert driving.status_code == 200 and driving.json()["emergency_stop"] is True
    assert driving.json()["attention"]["prime_advisory"] == 1
    assert driving.json()["attention"]["prime_integrity"] == 0
    assert "evidence" not in driving.json() and driving.json()["execution_authorized"] is False
    assert "Private source details" not in driving.text and "test-legacy" not in driving.text

    threads = "/api/weweb/owner-conversations"
    history = f"{threads}/{thread_id}/turns"
    assert client.get(threads, headers=outsider).status_code == 403
    assert client.get(threads, headers=bearer).json()[0]["conversation_id"] == str(thread_id)
    turn = client.get(history, headers=bearer)
    assert turn.headers["cache-control"] == "no-store"
    assert turn.json()[0]["evidence"]["source"] == "fixture"

    import base64
    import hashlib

    def forbidden_inference(*args, **kwargs):
        raise AssertionError("Owner browser messages must never call a provider")
    monkeypatch.setattr("app.services.owner_conversation.advisory_reply", forbidden_inference)
    fresh = str(uuid4())
    assert client.post(threads, headers=outsider, json={"conversation_id": fresh, "title": "Fixture"}).status_code == 403
    assert client.post(threads, headers=bearer, json={"conversation_id": fresh, "title": "Fixture"}).status_code == 201
    inbox = f"{threads}/{fresh}"
    dependency_turn = {"turn_id": str(uuid4()), "message": "What do I need before first revenue?"}
    response = client.post(f"{inbox}/turns", headers=bearer, json=dependency_turn)
    assert response.status_code == 201 and response.headers["cache-control"] == "no-store"
    result = response.json()
    assert result["evidence"]["source"] == "private_startup_dependency_guidance"
    assert result["evidence"]["startup_dependencies"] == plan_only
    assert result["evidence"]["model_connected"] is False
    assert client.post(f"{inbox}/turns", headers=bearer, json=dependency_turn).json() == result
    payload = {"turn_id": str(uuid4()), "message": "Review my operating options"}
    submitted = client.post(f"{inbox}/turns", headers=bearer, json=payload)
    assert submitted.status_code == 201, submitted.text
    assert submitted.headers["cache-control"] == "no-store"
    assert submitted.json()["execution_authorized"] is False
    assert client.post(f"{inbox}/turns", headers=bearer, json=payload).json() == submitted.json()
    assert client.post(f"{inbox}/turns", headers=bearer, json={**payload, "message": "Changed"}).status_code == 409
    assert client.post(f"{inbox}/turns", headers=bearer, json={
        **payload, "provider_data_class": "SYNTHETIC",
    }).status_code == 422
    historical_id = uuid4()
    with Session(engine) as db:
        db.add(OwnerTurn(id=historical_id, conversation_id=UUID(fresh), message="Historical response",
                         reply="Recorded earlier", evidence={"model_connected": True}, attachment_ids=[]))
        db.commit()
    assert client.post(f"{inbox}/turns", headers=bearer, json={
        "turn_id": str(historical_id), "message": "Historical response",
    }).status_code == 409
    historic_read = client.get(f"{inbox}/turns", headers=bearer)
    assert historic_read.status_code == 200
    assert any(item["turn_id"] == str(historical_id) and item["response_mode"] == "MODEL_ADVISORY_ONLY"
               for item in historic_read.json())

    content = b"Owner private attachment fixture"
    upload = {"attachment_id": str(uuid4()), "filename":"source.txt", "media_type":"text/plain",
              "sha256": hashlib.sha256(content).hexdigest(), "content_base64": base64.b64encode(content).decode()}
    attachment = client.post(f"{inbox}/attachments", headers=bearer, json=upload)
    assert attachment.status_code == 201, attachment.text
    assert client.post(f"{inbox}/attachments", headers=bearer, json=upload).json() == attachment.json()
    renamed = {**upload, "filename": "different.txt"}
    assert client.post(f"{inbox}/attachments", headers=bearer, json=renamed).status_code == 409
    assert client.get(f"{inbox}/attachments", headers=outsider).status_code == 403
    metadata = client.get(f"{inbox}/attachments", headers=bearer)
    assert metadata.headers["cache-control"] == "no-store"
    assert metadata.json() == [attachment.json()]
    assert "content_base64" not in metadata.text and upload["content_base64"] not in metadata.text
    attachment_root = f"{inbox}/attachments/{upload['attachment_id']}"
    assert client.post(f"{attachment_root}/extract", headers=outsider).status_code == 403
    extraction = client.post(f"{attachment_root}/extract", headers=bearer)
    assert extraction.status_code == 200, extraction.text
    assert extraction.json()["sent_to_provider"] is False

    schedule_route = f"/api/weweb/owner-specialist-schedules/{schedule_id}"
    assert client.get(schedule_route, headers=outsider).status_code == 403
    specialist = client.get(schedule_route, headers=bearer)
    assert specialist.status_code == 200, specialist.text
    assert specialist.headers["cache-control"] == "no-store"
    assert specialist.json()["report_event_id"] == report_id
    assert specialist.json()["execution_authorized"] is False

    from app.loki.evidence import artifact_digest
    from app.loki.models import LokiReview
    from app.models.specialist_assignment import SpecialistAssignment, SpecialistTrigger
    from app.pantheon.monitor import REPORT_EVENT as PANTHEON_REPORT_EVENT

    for model in (SpecialistAssignment, SpecialistTrigger, LokiReview):
        model.__table__.create(engine, checkfirst=True)
    report_index = "/api/weweb/owner-pantheon/reports"
    assert client.get(report_index).status_code == 401
    assert client.get(report_index, headers=outsider).status_code == 403
    assert client.get(report_index, headers=bearer).json()["reports"] == []
    scope = {"legacy_instance_id": "test-legacy", "business_id": "test-shop",
             "engine_id": "micro_saas", "jurisdiction": "CA-MB"}
    first, second = UUID(int=1), UUID(int=2)
    report_ref = "GOD-" + "a" * 64
    role = "TYR"
    evidence = {"assignment_id": str(first), "report_event_id": report_ref, "scope": scope, "role": role,
                "observed_at": instant.isoformat() + "Z", "status": "observed", "trigger": "CADENCE",
                "observations": {"approval_evidence": {"private": "Unprojected raw source"}}}
    digest = artifact_digest("pantheon_report", report_ref, evidence)
    with Session(engine) as db:
        for assignment_id, assigned_role, latest in ((first, role, report_ref), (second, "NJORD", "GOD-missing")):
            db.add(SpecialistAssignment(id=assignment_id, role=assigned_role, scope_key=assigned_role, scope=scope,
                                       state="active", cadence_seconds=300, next_due_at=instant,
                                       expires_at=instant + timedelta(hours=1), last_report_event_id=latest))
        db.add(LegacyOrchestrationEvent(
            event_id=report_ref, legacy_instance_id=scope["legacy_instance_id"], event_type=PANTHEON_REPORT_EVENT,
            message="Synthetic digest-bound report", payload_json=json.dumps({**evidence, "report_sha256": digest}),
        ))
        db.add(LokiReview(input_source="pantheon-assignment", artifact_type="pantheon_report",
                          heimdall_reference_id=report_ref, artifact_sha256=digest, raw_input=evidence))
        db.commit()
    result = client.get(report_index, params={"limit": 1}, headers=bearer)
    assert result.status_code == 200 and result.headers["cache-control"] == "no-store"
    page = result.json()
    [entry] = page["reports"]
    assert page["execution_authorized"] is False and page["next_after"] == str(first)
    assert entry["state"] == "VERIFIED_RECEIPT" and entry["report_sha256"] == digest and entry["scope"] == scope
    assert entry["independent_loki"]["status"] == "queued"
    assert "Unprojected raw source" not in result.text
    remaining = client.get(report_index, params={"after": page["next_after"]}, headers=bearer).json()
    assert remaining["reports"] == [{"assignment_id": str(second), "role": "NJORD", "state": "INTEGRITY_HOLD"}]
    assert remaining["next_after"] is None
    assert client.get(report_index, params={"role": "TYR"}, headers=bearer).json()["reports"] == [entry]

    pending = {"request_id": str(uuid4()), "source_sha256": upload["sha256"],
               "operation": "ACCEPT_LOCAL", "reason": "Synthetic local review"}
    request_url = f"{attachment_root}/requests"
    assert client.post(request_url, headers=outsider, json=pending).status_code == 403
    staged = client.post(request_url, headers=bearer, json=pending)
    assert staged.status_code == 201, staged.text
    assert staged.json()["status"] == "PENDING_MANDATE"
    assert client.post(request_url, headers=bearer, json=pending).json() == staged.json()
    assert client.post(request_url, headers=bearer, json={**pending, "reason": "Changed"}).status_code == 409
    assert client.get(f"{inbox}/attachments", headers=bearer).json()[0]["state"] == "QUARANTINED_UNREVIEWED"
    stale = client.post(request_url, headers=bearer,
                        json={**pending, "request_id": str(uuid4()), "operation": "REJECT"})
    assert stale.status_code == 201
    status = f"/api/weweb/owner-document-requests/{pending['request_id']}"
    approval = {"expected_sha256": staged.json()["request_sha256"]}
    assert client.post(status + "/apply", headers=bearer, json=approval).status_code == 401
    assert client.post(status + "/apply", headers={**bearer, **owner}, json=approval).status_code == 503
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    with Session(engine) as db:
        db.get(GoLiveState, 1).kill_switch_engaged = False
        db.commit()
    assert client.post(status + "/apply", headers={**bearer, **owner},
                       json={"expected_sha256": "0" * 64}).status_code == 409
    applied = client.post(status + "/apply", headers={**bearer, **owner}, json=approval)
    assert applied.status_code == 200, applied.text
    assert applied.json()["receipt"]["disposition"] == "ACCEPT_LOCAL"
    assert client.get(status, headers=bearer).json() == applied.json()
    assert client.post(status + "/apply", headers={**bearer, **owner}, json=approval).json() == applied.json()
    stale_apply = f"/api/weweb/owner-document-requests/{stale.json()['request']['request_id']}/apply"
    assert client.post(stale_apply, headers={**bearer, **owner},
                       json={"expected_sha256": stale.json()["request_sha256"]}).status_code == 409

    disposal = client.post(request_url, headers=bearer, json={
        **pending, "request_id": str(uuid4()), "operation": "DISPOSE",
    }).json()
    dispose_url = f"/api/weweb/owner-document-requests/{disposal['request']['request_id']}/apply"
    disposed = client.post(dispose_url, headers={**bearer, **owner},
                           json={"expected_sha256": disposal["request_sha256"]})
    assert disposed.status_code == 200, disposed.text
    assert disposed.json()["receipt"]["state"] == "DELETED"
    assert client.get(f"{inbox}/attachments", headers=bearer).json()[0]["state"] == "DELETED"

    access = f"{root}/{trial['tenant_id']}/access/wholesale_engine"
    assert client.get(access).status_code == 401
    assert client.get(access, headers=outsider).status_code == 404
    assert client.get(f"{root}/{uuid4()}/access/wholesale_engine", headers=bearer).status_code == 404
    assert client.get(access, headers=bearer).json()["has_access"]
    assert client.get(f"{root}/{trial['tenant_id']}/access/dispo_engine", headers=bearer).status_code == 404
    assert client.delete(f"{root}/{trial['entitlement_id']}", headers=owner).json()["revoked"]
    assert client.get(access, headers=bearer).status_code == 404
    assert client.post("/api/weweb/logout", headers=bearer).status_code == 200
    assert client.get(attention, headers=bearer).status_code == 401
    assert client.get(access, headers=bearer).status_code == 401
    assert client.get(briefing, headers=bearer).status_code == 401
    assert client.post(path, headers=bearer, json=plan).status_code == 401
    assert client.get(history, headers=bearer).status_code == 401
    assert client.get(f"{inbox}/attachments", headers=bearer).status_code == 401
