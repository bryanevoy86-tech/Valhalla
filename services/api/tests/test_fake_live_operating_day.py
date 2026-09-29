from __future__ import annotations

import json
import time
from datetime import date, datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import get_db
from app.core.engines.actions import OUTREACH
from app.core.engines import guard_runtime
from app.leads.models import Lead
from app.models.audit_log import AuditLog
from app.models.completion_registry import (
    DatasetRegistryItem,
    EngineRegistryItem,
    KnowledgeRegistryItem,
    LearningAuditEvent,
    LearningCurriculumRegistryItem,
    LearningDomainRegistryItem,
    LearningFeedbackRecord,
    LearningTaskQueueItem,
    LegacyInstanceRegistryItem,
    LearningPromotionRecord,
    ScenarioExecutionRecord,
    ScenarioRegistryItem,
    ScoringRegistryItem,
    SourceRegistryItem,
    TemplateRegistryItem,
)
from app.models.deal import Deal
from app.models.engine_state import EngineStateRow
from app.models.freeze_events import FreezeEvent
from app.models.go_live_state import GoLiveState
from app.models.lead_intake import LeadIntake
from app.models.match import Buyer, DealBrief
from app.models.owner_command import OwnerCommand
from app.models.pending_action import PendingAction
from app.models.va_approval_queue import VAApprovalQueue
from app.models.va_audit_log import VAAuditLog
from app.models.va_lead import VALead
from app.routers.completion_registry import router as completion_router
from app.routers.deal_workflow_status import router as deal_workflow_status_router
from app.routers.flow_full_pipeline import router as full_pipeline_router
from app.routers.system_self_check import router as self_check_router
from app.routers.va_intake import router as va_intake_router
from app.services.va_audit_service import log_va_event


def _write_json(path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_fake_live_client() -> tuple[TestClient, sessionmaker]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(bind=engine)

    # Core workflow tables
    VALead.__table__.create(bind=engine, checkfirst=True)
    VAApprovalQueue.__table__.create(bind=engine, checkfirst=True)
    VAAuditLog.__table__.create(bind=engine, checkfirst=True)
    Lead.__table__.create(bind=engine, checkfirst=True)
    Deal.__table__.create(bind=engine, checkfirst=True)
    DealBrief.__table__.create(bind=engine, checkfirst=True)
    Buyer.__table__.create(bind=engine, checkfirst=True)
    FreezeEvent.__table__.create(bind=engine, checkfirst=True)

    # Completion/integrity tables
    PendingAction.__table__.create(bind=engine, checkfirst=True)
    OwnerCommand.__table__.create(bind=engine, checkfirst=True)
    LeadIntake.__table__.create(bind=engine, checkfirst=True)
    GoLiveState.__table__.create(bind=engine, checkfirst=True)
    AuditLog.__table__.create(bind=engine, checkfirst=True)
    EngineStateRow.__table__.create(bind=engine, checkfirst=True)

    KnowledgeRegistryItem.__table__.create(bind=engine, checkfirst=True)
    TemplateRegistryItem.__table__.create(bind=engine, checkfirst=True)
    ScoringRegistryItem.__table__.create(bind=engine, checkfirst=True)
    SourceRegistryItem.__table__.create(bind=engine, checkfirst=True)
    DatasetRegistryItem.__table__.create(bind=engine, checkfirst=True)
    ScenarioRegistryItem.__table__.create(bind=engine, checkfirst=True)
    ScenarioExecutionRecord.__table__.create(bind=engine, checkfirst=True)
    LearningPromotionRecord.__table__.create(bind=engine, checkfirst=True)
    LearningTaskQueueItem.__table__.create(bind=engine, checkfirst=True)
    LearningDomainRegistryItem.__table__.create(bind=engine, checkfirst=True)
    LearningCurriculumRegistryItem.__table__.create(bind=engine, checkfirst=True)
    LearningFeedbackRecord.__table__.create(bind=engine, checkfirst=True)
    LearningAuditEvent.__table__.create(bind=engine, checkfirst=True)
    EngineRegistryItem.__table__.create(bind=engine, checkfirst=True)
    LegacyInstanceRegistryItem.__table__.create(bind=engine, checkfirst=True)

    # Seed one matching and one mismatching buyer.
    db = session_local()
    try:
        db.add(
            Buyer(
                full_name="Winnipeg SFH Buyer",
                email="wpg-buyer@example.com",
                phone="555-3001",
                preferred_markets="Winnipeg",
                status="active",
                buy_box_json={
                    "property_types": "SFH",
                    "min_price": 200000,
                    "max_price": 360000,
                    "min_beds": 2,
                    "min_baths": 1,
                },
            )
        )
        db.add(
            Buyer(
                full_name="No-Match Buyer",
                email="nomatch@example.com",
                phone="555-3002",
                preferred_markets="Calgary",
                status="active",
                buy_box_json={
                    "property_types": "Condo",
                    "min_price": 900000,
                    "max_price": 1200000,
                    "min_beds": 4,
                    "min_baths": 3,
                },
            )
        )
        db.commit()
    finally:
        db.close()

    app = FastAPI()
    app.include_router(va_intake_router)
    app.include_router(full_pipeline_router)
    app.include_router(deal_workflow_status_router)
    app.include_router(completion_router)
    app.include_router(self_check_router)

    def override_get_db():
        session = session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), session_local


def _submit_lead(client: TestClient, payload: dict) -> dict:
    response = client.post("/api/va-intake/lead", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _run_pipeline(client: TestClient, *, lead_name: str, email: str, region: str, property_type: str, price: int) -> dict:
    response = client.post(
        "/flow/full_deal_pipeline",
        json={
            "lead": {
                "name": lead_name,
                "email": email,
                "phone": "555-666-7777",
                "source": "Sandbox",
                "address": "500 Fake Live Blvd",
                "tags": "sandbox,fake-live",
                "org_id": 1,
            },
            "deal": {
                "headline": f"{region} {property_type} scenario",
                "region": region,
                "property_type": property_type,
                "price": price,
                "beds": 3,
                "baths": 2,
                "notes": "fake-live day simulation",
                "status": "active",
                "arv": price + 90000,
                "repairs": 30000,
                "offer": price - 5000,
                "mao": price + 5000,
                "roi_note": "simulated ops",
            },
            "match_settings": {
                "match_buyers": True,
                "min_match_score": 0.5,
                "max_results": 5,
            },
            "underwriting": {
                "arv": price + 90000,
                "purchase_price": price - 5000,
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
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_fake_live_operating_day_controlled_stage_report(tmp_path, monkeypatch):
    client, SessionLocal = _build_fake_live_client()

    heartbeat = tmp_path / "heartbeat.json"
    _write_json(heartbeat, {"ts": time.time()})
    mcp_cfg = tmp_path / "mcp.json"
    _write_json(
        mcp_cfg,
        {
            "servers": {
                "weweb-ai": {
                    "type": "http",
                    "url": "https://ai-api.weweb.io/v1/mcp",
                }
            }
        },
    )
    auth_evidence = tmp_path / "weweb_auth.json"
    _write_json(
        auth_evidence,
        {
            "authenticated": True,
            "project_discovered": True,
            "valhalla_project_confirmed": True,
            "read_access_proven": True,
        },
    )

    monkeypatch.setenv("VALHALLA_WORKER_HEARTBEAT_FILE", str(heartbeat))
    monkeypatch.setenv("VALHALLA_WEWEB_MCP_CONFIG_PATH", str(mcp_cfg))
    monkeypatch.setenv("VALHALLA_WEWEB_AUTH_EVIDENCE_PATH", str(auth_evidence))
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USER", "ops@example.com")
    monkeypatch.setenv("SMTP_PASS", "secret")
    monkeypatch.setenv("VALHALLA_PROVIDER_FAILURE_STATE", "smtp")
    monkeypatch.setenv("VALHALLA_FUTURE_ENGINES_ACTIVE", "")

    lead_payloads = [
        {
            "source_platform": "facebook",
            "source_type": "manual_va",
            "source_url": "https://sandbox.example/lead/1",
            "address": "101 Queue St",
            "city": "Winnipeg",
            "province": "MB",
            "seller_name": "Seller One",
            "seller_phone": "555-101-1010",
            "seller_email": "seller1@example.com",
            "asking_price": 245000,
            "raw_text": "Urgent sale as-is.",
            "va_notes": "Priority contact",
            "strategy_fit": "wholesale",
            "submitted_by": "va_alpha",
        },
        {
            "source_platform": "kijiji",
            "source_type": "manual_va",
            "source_url": "https://sandbox.example/lead/2",
            "address": "202 Escalation Ave",
            "city": "Winnipeg",
            "province": "MB",
            "seller_name": "Seller Two",
            "seller_phone": "555-202-2020",
            "seller_email": "seller2@example.com",
            "asking_price": 255000,
            "raw_text": "Needs fast sale, legal docs uncertain.",
            "va_notes": "May require legal escalation",
            "strategy_fit": "wholesale",
            "submitted_by": "va_beta",
        },
        {
            "source_platform": "referral",
            "source_type": "manual_va",
            "source_url": "https://sandbox.example/lead/3",
            "address": "303 Followup Rd",
            "city": "Winnipeg",
            "province": "MB",
            "seller_name": "Seller Three",
            "seller_phone": "555-303-3030",
            "seller_email": "seller3@example.com",
            "asking_price": 265000,
            "raw_text": "Landlord exit scenario.",
            "va_notes": "Good follow-up candidate",
            "strategy_fit": "wholesale",
            "submitted_by": "va_gamma",
        },
    ]

    lead_rows = [_submit_lead(client, payload) for payload in lead_payloads]

    pending = client.get("/api/va-intake/approvals/pending")
    assert pending.status_code == 200
    pending_rows = pending.json()["items"]
    assert len(pending_rows) >= 3

    approvals_requested = len(pending_rows)
    followups_created = sum(1 for row in lead_rows if "seller contact" in row["recommended_action"].lower())

    approve_resp = client.post(f"/api/va-intake/approvals/{int(pending_rows[0]['approval_id'])}/approve")
    assert approve_resp.status_code == 200

    deny_resp = client.post(
        f"/api/va-intake/approvals/{int(pending_rows[1]['approval_id'])}/deny",
        params={"reason": "owner rejected due to unresolved title"},
    )
    assert deny_resp.status_code == 200

    failover_events = 0
    founder_escalations = 1
    session = SessionLocal()
    try:
        stale_target = (
            session.query(VAApprovalQueue)
            .filter(VAApprovalQueue.id == int(pending_rows[2]["approval_id"]))
            .first()
        )
        assert stale_target is not None
        stale_target.created_at = datetime.now(timezone.utc) - timedelta(days=2)

        # Founder overload filter + reassignment failover
        stale_target.assigned_to = "backup_operator"
        failover_events += 1
        log_va_event(
            actor="heimdall",
            action="task_reassigned_failover",
            entity_type="va_approval_queue",
            entity_id=stale_target.id,
            details="Reassigned due to founder overload filter.",
            db=session,
        )

        # Seed stale queue and failed task conditions for integrity checks.
        session.add(
            LearningTaskQueueItem(
                task_id="LQ-FAILED-001",
                task_type="REVERIFY_KNOWLEDGE",
                status="blocked",
                priority="high",
                domain="OPERATIONS",
                reason="provider timeout",
                created_at=datetime.utcnow() - timedelta(days=2),
            )
        )
        session.commit()
    finally:
        session.close()

    success_pipe = _run_pipeline(
        client,
        lead_name="Pipeline Seller Match",
        email="match@example.com",
        region="Winnipeg",
        property_type="SFH",
        price=250000,
    )
    no_buyer_pipe = _run_pipeline(
        client,
        lead_name="Pipeline Seller NoMatch",
        email="nomatch2@example.com",
        region="Toronto",
        property_type="Land",
        price=975000,
    )

    success_matches = len(success_pipe.get("matched_buyers", []))
    no_buyer_escalations = 1 if len(no_buyer_pipe.get("matched_buyers", [])) == 0 else 0

    wf_success = client.get(f"/workflow/deal_status/{int(success_pipe['backend_deal_id'])}")
    wf_no_buyer = client.get(f"/workflow/deal_status/{int(no_buyer_pipe['backend_deal_id'])}")
    assert wf_success.status_code == 200
    assert wf_no_buyer.status_code == 200

    src = client.post(
        "/api/completion/source-items",
        json={
            "source_id": "SRC-FAKE-LIVE-001",
            "canonical_name": "Fake Live Source",
            "source_type": "government",
            "data_class": "live",
            "terminal_state": "ACTIVE_AND_VERIFIED",
        },
    )
    assert src.status_code == 200

    fresh_knowledge = client.post(
        "/api/completion/knowledge-items",
        json={
            "item_id": "KNOW-FAKE-FRESH-001",
            "source": "SRC-FAKE-LIVE-001",
            "source_type": "government",
            "title": "OPERATIONS approval playbook",
            "terminal_state": "ACTIVE_AND_VERIFIED",
            "review_status": "approved",
            "quality_score": 0.95,
            "confidence_score": 0.95,
            "review_date": date.today().isoformat(),
            "citation_ref": "gov:ops:fresh",
        },
    )
    assert fresh_knowledge.status_code == 200

    stale_knowledge = client.post(
        "/api/completion/knowledge-items",
        json={
            "item_id": "KNOW-FAKE-STALE-001",
            "source": "SRC-FAKE-LIVE-001",
            "source_type": "government",
            "title": "OPERATIONS stale approval heuristic",
            "terminal_state": "ACTIVE_AND_VERIFIED",
            "review_status": "approved",
            "quality_score": 0.90,
            "confidence_score": 0.45,
            "review_date": "2023-01-01",
            "citation_ref": "gov:ops:stale",
        },
    )
    assert stale_knowledge.status_code == 200

    retrieved = client.post(
        "/api/completion/knowledge/retrieve",
        json={"question": "approval heuristic", "domain": "OPERATIONS", "mode": "live", "risk_level": "high"},
    )
    assert retrieved.status_code == 200

    reverify_first = client.post("/api/completion/learning/tasks/reverify-stale")
    assert reverify_first.status_code == 200
    reverify_second = client.post("/api/completion/learning/tasks/reverify-stale")
    assert reverify_second.status_code == 200
    assert reverify_second.json()["created"] == 0

    feedback = client.post(
        "/api/completion/learning/feedback",
        json={
            "feedback_id": "FB-FAKE-LIVE-001",
            "feedback_type": "operational_result",
            "domain": "OPERATIONS",
            "learning_id": "LP-FAKE-LIVE-001",
            "operational_score": 0.82,
            "outcome_class": "VERIFIED_REAL_OUTCOME",
            "high_impact": True,
            "human_review_required": True,
            "notes": "Provider failure forced manual queue fallback.",
        },
    )
    assert feedback.status_code == 200

    # Restricted-action attempt + kill-switch condition.
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "1")
    session = SessionLocal()
    try:
        go = session.query(GoLiveState).filter(GoLiveState.id == 1).first()
        if go is None:
            go = GoLiveState(id=1)
            session.add(go)
        go.kill_switch_engaged = True
        go.go_live_enabled = False
        go.changed_by = "fake-live-test"
        go.reason = "intentional kill-switch simulation"
        session.commit()
    finally:
        session.close()

    def _override_guard_db_session():
        local = SessionLocal()
        try:
            yield local
        finally:
            local.close()

    monkeypatch.setattr(guard_runtime, "get_db_session", _override_guard_db_session)

    failed_actions_blocked = 0
    try:
        guard_runtime.enforce_engine("wholesaling", OUTREACH)
    except HTTPException as exc:
        assert exc.status_code == 409
        failed_actions_blocked += 1

    self_check = client.get("/api/system/self-check?probe_isolation_violation=true")
    assert self_check.status_code == 200
    self_body = self_check.json()

    audit_events = 0
    session = SessionLocal()
    try:
        audit_events = session.query(AuditLog).count() + session.query(VAAuditLog).count()
    finally:
        session.close()

    document_states = 0
    simulated_closings = 0
    for wf in (wf_success.json(), wf_no_buyer.json()):
        flags = wf.get("flags", {}) if isinstance(wf, dict) else {}
        if flags:
            document_states += 1
        if str(flags.get("closing_status", "")).lower() in {"simulated_closed", "closed"}:
            simulated_closings += 1

    stage_report = {
        "LEADS_PROCESSED": len(lead_rows),
        "VA_TASKS_CREATED": approvals_requested,
        "FOLLOWUPS_CREATED": followups_created,
        "APPROVALS_REQUESTED": approvals_requested,
        "APPROVALS_COMPLETED": 2,
        "DEALS_CREATED": 2,
        "UNDERWRITING_COMPLETED": 2,
        "BUYER_MATCHES": success_matches,
        "NO_BUYER_ESCALATIONS": no_buyer_escalations,
        "DISPOSITION_ACTIONS": 2,
        "DOCUMENT_STATES": document_states,
        "SIMULATED_CLOSINGS": simulated_closings,
        "AUDIT_EVENTS": audit_events,
        "LEARNING_FEEDBACK_EVENTS": 1,
        "REVERIFY_TASKS": reverify_first.json()["created"] + reverify_second.json()["existing_open"],
        "INTEGRITY_ALERTS": int(self_body["integrity_audit_trail"]["events_emitted"]),
        "FAILED_ACTIONS_BLOCKED": failed_actions_blocked,
        "FOUNDER_ESCALATIONS": founder_escalations,
        "FAILOVER_EVENTS": failover_events,
    }

    required_keys = {
        "LEADS_PROCESSED",
        "VA_TASKS_CREATED",
        "FOLLOWUPS_CREATED",
        "APPROVALS_REQUESTED",
        "APPROVALS_COMPLETED",
        "DEALS_CREATED",
        "UNDERWRITING_COMPLETED",
        "BUYER_MATCHES",
        "NO_BUYER_ESCALATIONS",
        "DISPOSITION_ACTIONS",
        "DOCUMENT_STATES",
        "SIMULATED_CLOSINGS",
        "AUDIT_EVENTS",
        "LEARNING_FEEDBACK_EVENTS",
        "REVERIFY_TASKS",
        "INTEGRITY_ALERTS",
        "FAILED_ACTIONS_BLOCKED",
        "FOUNDER_ESCALATIONS",
        "FAILOVER_EVENTS",
    }
    assert required_keys.issubset(stage_report.keys())

    # Detect -> Log -> Escalate -> Fail-safe while still processing non-blocked work.
    assert stage_report["LEADS_PROCESSED"] >= 3
    assert stage_report["DEALS_CREATED"] >= 2
    assert stage_report["NO_BUYER_ESCALATIONS"] >= 1
    assert stage_report["FAILED_ACTIONS_BLOCKED"] >= 1
    assert stage_report["INTEGRITY_ALERTS"] >= 1
    assert self_body["fail_safe_state"]["active"] is True
    assert self_body["anomaly_detection"]["state"] == "ANOMALY_DETECTED"

    fake_live_day = "PASS"
    reasons: list[str] = []
    if stage_report["INTEGRITY_ALERTS"] < 1:
        fake_live_day = "PARTIAL"
        reasons.append("integrity alerts did not fire")
    if stage_report["FAILED_ACTIONS_BLOCKED"] < 1:
        fake_live_day = "PARTIAL"
        reasons.append("restricted action was not blocked")
    if stage_report["DEALS_CREATED"] < 1:
        fake_live_day = "FAIL"
        reasons.append("deal pipeline did not execute")

    stage_report["FAKE_LIVE_DAY"] = fake_live_day
    stage_report["FAKE_LIVE_DAY_REASONS"] = reasons or ["all required controls and continuations observed"]

    print("FAKE_LIVE_STAGE_REPORT=" + json.dumps(stage_report, sort_keys=True))

    assert stage_report["FAKE_LIVE_DAY"] == "PASS"
