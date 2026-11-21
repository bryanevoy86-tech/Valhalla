from datetime import datetime, timedelta, timezone
import json
from uuid import uuid4

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
    assert client.post(path, json=plan).status_code == 401
    assert client.post(path, headers=outsider, json=plan).status_code == 403
    quote = client.post(path, headers=bearer, json=plan)
    assert quote.status_code == 200, quote.text
    assert quote.headers["cache-control"] == "no-store"
    budget = quote.json()
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

    from app.models.owner_conversation import OwnerAttachment, OwnerAttachmentExtraction, OwnerConversation, OwnerTurn

    from app.routers.prime_specialist_schedules import REPORT_EVENT, shadow_report_digest

    for model in (LearningTaskQueueItem, LegacyOrchestrationEvent, GoLiveState, PrimeSpecialistSchedule,
                  PrimeScheduleTrigger, OwnerConversation, OwnerTurn, OwnerAttachment, OwnerAttachmentExtraction):
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
    content = b"Owner private attachment fixture"
    upload = {"attachment_id": str(uuid4()), "filename":"source.txt", "media_type":"text/plain",
              "sha256": hashlib.sha256(content).hexdigest(), "content_base64": base64.b64encode(content).decode()}
    attachment = client.post(f"{inbox}/attachments", headers=bearer, json=upload)
    assert attachment.status_code == 201, attachment.text
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
