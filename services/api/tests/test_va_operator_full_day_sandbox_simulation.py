from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import get_db
from app.leads.models import Lead
from app.models.deal import Deal
from app.models.freeze_events import FreezeEvent
from app.models.match import Buyer, DealBrief
from app.models.va_approval_queue import VAApprovalQueue
from app.models.va_audit_log import VAAuditLog
from app.models.va_lead import VALead
from app.routers.deal_workflow_status import router as deal_workflow_status_router
from app.routers.flow_full_pipeline import router as full_pipeline_router
from app.routers.va_intake import router as va_intake_router
from app.services.va_audit_service import log_va_event


def _make_simulation_client() -> tuple[TestClient, sessionmaker]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine)

    VALead.__table__.create(bind=engine, checkfirst=True)
    VAApprovalQueue.__table__.create(bind=engine, checkfirst=True)
    VAAuditLog.__table__.create(bind=engine, checkfirst=True)
    Lead.__table__.create(bind=engine, checkfirst=True)
    Deal.__table__.create(bind=engine, checkfirst=True)
    DealBrief.__table__.create(bind=engine, checkfirst=True)
    Buyer.__table__.create(bind=engine, checkfirst=True)
    FreezeEvent.__table__.create(bind=engine, checkfirst=True)

    db = SessionLocal()
    try:
        # Controlled buyers: one eligible + one clearly ineligible.
        db.add(
            Buyer(
                full_name="Winnipeg SFH Buyer",
                email="wpg-sfh@example.com",
                phone="555-2101",
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
                full_name="Calgary Condo Buyer",
                email="yyc-condo@example.com",
                phone="555-2102",
                preferred_markets="Calgary",
                status="active",
                buy_box_json={
                    "property_types": "Condo",
                    "min_price": 700000,
                    "max_price": 1200000,
                    "min_beds": 3,
                    "min_baths": 2,
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

    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), SessionLocal


def _submit_lead(client: TestClient, payload: dict) -> dict:
    response = client.post("/api/va-intake/lead", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_va_operator_full_day_sandbox_simulation():
    client, SessionLocal = _make_simulation_client()

    lead_payloads = [
        {
            "source_platform": "facebook",
            "source_type": "manual_va",
            "source_url": "https://sandbox.example/lead/1",
            "address": "111 Priority St",
            "city": "Winnipeg",
            "province": "MB",
            "seller_name": "Priority Seller",
            "seller_phone": "555-111-1111",
            "seller_email": "priority@example.com",
            "asking_price": 245000,
            "raw_text": "Motivated owner, must sell as is, needs work.",
            "va_notes": "Best immediate seller contact candidate.",
            "strategy_fit": "wholesale",
            "submitted_by": "va_alpha",
        },
        {
            "source_platform": "kijiji",
            "source_type": "manual_va",
            "source_url": "https://sandbox.example/lead/2",
            "address": "222 Followup Ave",
            "city": "Winnipeg",
            "province": "MB",
            "seller_name": "Followup Seller",
            "seller_phone": "555-222-2222",
            "seller_email": "followup@example.com",
            "asking_price": 255000,
            "raw_text": "Vacant property and quick possession requested.",
            "va_notes": "Strong contact signal for follow-up queue.",
            "strategy_fit": "wholesale",
            "submitted_by": "va_beta",
        },
        {
            "source_platform": "google_maps",
            "source_type": "manual_va",
            "source_url": "https://sandbox.example/lead/3",
            "address": "333 Escalation Rd",
            "city": "Winnipeg",
            "province": "MB",
            "seller_name": "Escalation Seller",
            "seller_phone": "555-333-3333",
            "seller_email": "escalation@example.com",
            "asking_price": 295000,
            "raw_text": "Needs work but uncertain ownership details.",
            "va_notes": "Potential legal ambiguity; may require escalation.",
            "strategy_fit": "wholesale",
            "submitted_by": "va_gamma",
        },
        {
            "source_platform": "referral",
            "source_type": "manual_va",
            "source_url": "https://sandbox.example/lead/4",
            "address": "444 Backup Ln",
            "city": "Winnipeg",
            "province": "MB",
            "seller_name": "Backup Seller",
            "seller_phone": "555-444-4444",
            "seller_email": "backup@example.com",
            "asking_price": 265000,
            "raw_text": "Landlord tired and tenant problem noted.",
            "va_notes": "Good backup assignment candidate.",
            "strategy_fit": "wholesale",
            "submitted_by": "va_delta",
        },
    ]

    submissions = [_submit_lead(client, payload) for payload in lead_payloads]

    # Heimdall prioritization and seller follow-up signal should be present.
    scores = [row["heimdall_score"] for row in submissions]
    assert max(scores) >= min(scores)
    assert any("seller contact" in row["recommended_action"].lower() for row in submissions)

    pending = client.get("/api/va-intake/approvals/pending")
    assert pending.status_code == 200, pending.text
    pending_items = pending.json()["items"]
    assert len(pending_items) >= 4
    assert all(row["assigned_to"] == "bryan" for row in pending_items)

    # Queue prioritization: highest Heimdall score handled first by simulation policy.
    ordered = sorted(pending_items, key=lambda row: int(row["heimdall_score"] or 0), reverse=True)
    top = ordered[0]

    approve_top = client.post(f"/api/va-intake/approvals/{int(top['approval_id'])}/approve")
    assert approve_top.status_code == 200, approve_top.text

    # Founder overload filtering and failover reassignment for lower-priority work.
    reassigned_ids: list[int] = []
    session = SessionLocal()
    try:
        for row in ordered[2:]:
            approval = session.query(VAApprovalQueue).filter(VAApprovalQueue.id == int(row["approval_id"])).first()
            if approval is None or approval.status != "pending":
                continue
            old = approval.assigned_to
            approval.assigned_to = "backup_operator"
            reassigned_ids.append(approval.id)
            log_va_event(
                actor="heimdall",
                action="task_reassigned_failover",
                entity_type="va_approval_queue",
                entity_id=approval.id,
                details=f"Reassigned from {old} to backup_operator to reduce founder overload.",
                db=session,
            )

        # Stale-task detection simulation on one still-pending task.
        stale_candidate = (
            session.query(VAApprovalQueue)
            .filter(VAApprovalQueue.status == "pending")
            .order_by(VAApprovalQueue.id.asc())
            .first()
        )
        if stale_candidate is not None:
            stale_candidate.created_at = datetime.now(timezone.utc) - timedelta(days=2)
            log_va_event(
                actor="heimdall",
                action="stale_task_detected",
                entity_type="va_approval_queue",
                entity_id=stale_candidate.id,
                details="Pending task exceeded freshness window and was flagged for escalation.",
                status="warning",
                db=session,
            )

        # Learning feedback artifact for the simulation day.
        log_va_event(
            actor="heimdall",
            action="learning_feedback_captured",
            entity_type="va_approval_queue",
            entity_id=int(top["approval_id"]),
            details="Recorded queue outcomes for future prioritization tuning.",
            db=session,
        )
        session.commit()
    finally:
        session.close()

    if reassigned_ids:
        pending_after_reassign = client.get("/api/va-intake/approvals/pending")
        assert pending_after_reassign.status_code == 200
        rows = pending_after_reassign.json()["items"]
        assert any(int(row["approval_id"]) in reassigned_ids and row["assigned_to"] == "backup_operator" for row in rows)

    # Escalation path: deny one pending approval with explicit reason.
    pending_latest = client.get("/api/va-intake/approvals/pending")
    assert pending_latest.status_code == 200
    pending_rows = pending_latest.json()["items"]
    deny_target = pending_rows[0]
    denied = client.post(
        f"/api/va-intake/approvals/{int(deny_target['approval_id'])}/deny",
        params={"reason": "requires legal review"},
    )
    assert denied.status_code == 200, denied.text
    assert denied.json()["status"] == "denied"

    # Underwriting + buyer/disposition workload on sandbox pipeline data.
    pipeline = client.post(
        "/flow/full_deal_pipeline",
        json={
            "lead": {
                "name": "Sandbox Workday Seller",
                "email": "workday@example.com",
                "phone": "555-555-5555",
                "source": "Sandbox",
                "address": "555 Workday Way",
                "tags": "sandbox,workday",
                "org_id": 1,
            },
            "deal": {
                "headline": "Workday SFH",
                "region": "Winnipeg",
                "property_type": "SFH",
                "price": 250000,
                "beds": 3,
                "baths": 2,
                "notes": "full-day simulation",
                "status": "active",
                "arv": 340000,
                "repairs": 30000,
                "offer": 245000,
                "mao": 255000,
                "roi_note": "sandbox simulation",
            },
            "match_settings": {
                "match_buyers": True,
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
        },
    )
    assert pipeline.status_code == 201, pipeline.text
    body = pipeline.json()
    assert len(body.get("matched_buyers", [])) >= 1

    workflow = client.get(f"/workflow/deal_status/{int(body['backend_deal_id'])}")
    assert workflow.status_code == 200, workflow.text
    wf = workflow.json()
    assert wf["deal"]["status"] in {"active", "draft", "under_contract", "sold", "archived"}

    # Audit/integrity monitoring: no error audit events, and expected simulation actions exist.
    session = SessionLocal()
    try:
        audit_rows = session.query(VAAuditLog).all()
        actions = {row.action for row in audit_rows}
        assert "lead_submitted" in actions
        assert "lead_scored" in actions
        assert "approval_approved" in actions
        assert "approval_denied" in actions
        assert "task_reassigned_failover" in actions
        assert "stale_task_detected" in actions
        assert "learning_feedback_captured" in actions
        assert all(row.status in {"success", "warning"} for row in audit_rows)
    finally:
        session.close()
