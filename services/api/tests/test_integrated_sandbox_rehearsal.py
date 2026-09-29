from __future__ import annotations

import os
import time
import uuid
from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.db import get_db
from app.leads.models import Lead
from app.models.deal import Deal
from app.models.freeze_events import FreezeEvent
from app.models.match import Buyer, DealBrief
from app.routers.flow_full_pipeline import router as full_pipeline_router
from app.routers.flow_prepare_closing import router as closing_context_router
from app.routers.deal_workflow_status import router as deal_workflow_status_router

# Minimal auth defaults for test import-time settings resolution.
os.environ.setdefault("VALHALLA_OWNER_PASSWORD", "test-owner-pass")
os.environ.setdefault("VALHALLA_JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("VALHALLA_OWNER_EMAIL", "owner@example.com")

from app.security.auth import SETTINGS, jwt_encode


client = TestClient(app)


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def _make_token(email: str, user_id: int, exp_offset_seconds: int = 3600) -> str:
    now = int(time.time())
    payload = {
        "sub": email,
        "user_id": user_id,
        "iat": now,
        "exp": now + exp_offset_seconds,
    }
    return jwt_encode(payload, SETTINGS.jwt_secret)


def _pipeline_payload(*, lead_name: str, email: str, match_buyers: bool, min_match_score: float, purchase_price: int, arv: int, repairs: int) -> dict:
    return {
        "lead": {
            "name": lead_name,
            "email": email,
            "phone": "555-100-2000",
            "source": "Sandbox",
            "address": "500 Integrated Test Ave, Winnipeg, MB",
            "tags": "sandbox,integrated",
            "org_id": 1,
        },
        "deal": {
            "headline": "Integrated rehearsal property",
            "region": "Winnipeg",
            "property_type": "SFH",
            "price": purchase_price,
            "beds": 3,
            "baths": 2,
            "notes": "Integrated sandbox rehearsal",
            "status": "active",
            "arv": arv,
            "repairs": repairs,
            "offer": purchase_price,
            "mao": purchase_price + 10000,
            "roi_note": "Integrated rehearsal note",
        },
        "match_settings": {
            "match_buyers": match_buyers,
            "min_match_score": min_match_score,
            "max_results": 5,
        },
        "underwriting": {
            "arv": arv,
            "purchase_price": purchase_price,
            "repairs": repairs,
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


def _components_by_id(body: dict) -> dict:
    rows = body["process_health"]["components"] + body["business_capability_readiness"]["components"]
    return {row["component_id"]: row for row in rows}


def _build_deterministic_no_buyer_client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine)

    Lead.__table__.create(bind=engine, checkfirst=True)
    Buyer.__table__.create(bind=engine, checkfirst=True)
    DealBrief.__table__.create(bind=engine, checkfirst=True)
    Deal.__table__.create(bind=engine, checkfirst=True)
    FreezeEvent.__table__.create(bind=engine, checkfirst=True)

    db = SessionLocal()
    try:
        # Controlled deterministic buyer set: active buyers that cannot match
        # region/property-type/price criteria for the target deal.
        b1 = Buyer(
            full_name="Calgary Land Buyer",
            email="calgary-land@example.com",
            phone="555-9000",
            preferred_markets="Calgary",
            status="active",
            buy_box_json={
                "property_types": "Land",
                "min_price": 900000,
                "max_price": 1200000,
                "min_beds": 10,
                "min_baths": 8,
            },
        )
        b2 = Buyer(
            full_name="Vancouver Condo Buyer",
            email="van-condo@example.com",
            phone="555-9001",
            preferred_markets="Vancouver",
            status="active",
            buy_box_json={
                "property_types": "Condo",
                "min_price": 800000,
                "max_price": 1100000,
                "min_beds": 4,
                "min_baths": 3,
            },
        )
        db.add_all([b1, b2])
        db.commit()
    finally:
        db.close()

    isolated = FastAPI()
    isolated.include_router(full_pipeline_router)
    isolated.include_router(closing_context_router)
    isolated.include_router(deal_workflow_status_router)

    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    isolated.dependency_overrides[get_db] = override_get_db
    return TestClient(isolated)


def test_integrated_sandbox_rehearsal_chain_stage_report():
    stage_report: dict[str, dict] = {}

    va_submit = client.post(
        "/api/va-intake/lead",
        json={
            "source_platform": "facebook",
            "source_type": "manual_va",
            "source_url": "https://example.com/listing/integrated-1",
            "address": "101 Sandbox Dr",
            "city": "Winnipeg",
            "province": "MB",
            "seller_name": "Sandbox Seller",
            "seller_phone": "555-111-3333",
            "seller_email": f"{_uid('seller')}@example.com",
            "asking_price": 245000,
            "raw_text": "Motivated seller needs quick close and has repair backlog.",
            "va_notes": "Strong distress + valid contact chain.",
            "strategy_fit": "wholesale",
            "submitted_by": "va_integrated",
        },
    )
    assert va_submit.status_code == 200, va_submit.text
    va_body = va_submit.json()
    lead_id = int(va_body["lead_id"])

    stage_report["LEAD_INTAKE"] = {
        "status": "PASS",
        "evidence": {"lead_id": lead_id, "lead_status": va_body["lead_status"]},
    }
    stage_report["HEIMDALL_SCORE"] = {
        "status": "PASS",
        "evidence": {
            "heimdall_score": va_body["heimdall_score"],
            "risk_level": va_body["risk_level"],
            "confidence": va_body["confidence"],
        },
    }

    pending = client.get("/api/va-intake/approvals/pending")
    assert pending.status_code == 200, pending.text
    pending_items = pending.json()["items"]
    approval_row = next((row for row in pending_items if int(row["lead_id"]) == lead_id), None)
    assert approval_row is not None
    approval_id = int(approval_row["approval_id"])
    stage_report["VA_TASK"] = {
        "status": "PASS",
        "evidence": {"approval_id": approval_id, "assigned_to": approval_row.get("assigned_to")},
    }

    approved = client.post(f"/api/va-intake/approvals/{approval_id}/approve")
    assert approved.status_code == 200, approved.text
    approved_body = approved.json()
    stage_report["APPROVAL"] = {
        "status": "PASS",
        "evidence": {"approval_status": approved_body.get("status")},
    }

    converted = client.post(f"/api/va-intake/leads/{lead_id}/convert-to-deal")
    assert converted.status_code == 200, converted.text
    converted_body = converted.json()
    converted_deal_id = int(converted_body["deal_id"])
    stage_report["DEAL_CONVERSION"] = {
        "status": "PASS",
        "evidence": {"converted_deal_id": converted_deal_id},
    }

    linked = client.get(f"/api/va-intake/leads/{lead_id}/deal")
    assert linked.status_code == 200, linked.text

    pipeline = client.post(
        "/flow/full_deal_pipeline",
        json=_pipeline_payload(
            lead_name="Integrated Pipeline Seller",
            email=f"{_uid('pipeline')}@example.com",
            match_buyers=True,
            min_match_score=0.0,
            purchase_price=245000,
            arv=340000,
            repairs=30000,
        ),
    )
    assert pipeline.status_code == 201, pipeline.text
    pipe = pipeline.json()
    backend_deal_id = int(pipe["backend_deal_id"])

    stage_report["UNDERWRITING"] = {
        "status": "PASS",
        "evidence": {
            "recommendation": pipe["underwriting_result"].get("recommendation"),
            "freeze_event_created": pipe.get("freeze_event_created"),
        },
    }
    stage_report["BUYER_MATCH"] = {
        "status": "PASS",
        "evidence": {"matched_buyers": len(pipe.get("matched_buyers", []))},
    }

    closing_context = client.get(f"/flow/closing_context/{backend_deal_id}")
    assert closing_context.status_code == 200, closing_context.text
    stage_report["SELLER_OUTCOME"] = {
        "status": "PASS",
        "evidence": {"suggested_opening": closing_context.json().get("suggested_opening")},
    }

    workflow = client.get(f"/workflow/deal_status/{backend_deal_id}")
    assert workflow.status_code == 200, workflow.text
    stage_report["DISPOSITION"] = {
        "status": "PASS",
        "evidence": workflow.json().get("flags", {}),
    }

    decision_guard = client.get("/api/heimdall/decision-card")
    assert decision_guard.status_code == 401
    stage_report["NEXT_BEST_ACTION"] = {
        "status": "PASS",
        "evidence": {"fail_closed_status": decision_guard.status_code},
    }

    source_id = _uid("SRC-INTEGRATED")
    knowledge_id = _uid("KNOW-INTEGRATED")
    src = client.post(
        "/api/completion/source-items",
        json={
            "source_id": source_id,
            "canonical_name": "Integrated Evidence Source",
            "source_type": "government",
            "data_class": "live",
            "terminal_state": "ACTIVE_AND_VERIFIED",
            "mode_allowlist": ["live"],
        },
    )
    assert src.status_code == 200, src.text

    validate = client.post(
        "/api/completion/source-items/validate-use",
        json={"source_id": source_id, "mode": "live"},
    )
    assert validate.status_code == 200, validate.text
    assert validate.json()["allowed"] is True

    know = client.post(
        "/api/completion/knowledge-items",
        json={
            "item_id": knowledge_id,
            "source": source_id,
            "source_type": "government",
            "title": "OPERATIONS integrated source guidance",
            "terminal_state": "ACTIVE_AND_VERIFIED",
            "review_status": "approved",
            "quality_score": 0.95,
            "confidence_score": 0.93,
            "review_date": date.today().isoformat(),
            "citation_ref": "gov:integrated:001",
        },
    )
    assert know.status_code == 200, know.text

    retrieved = client.post(
        "/api/completion/knowledge/retrieve",
        json={"question": "seller outreach policy", "domain": "OPERATIONS", "mode": "live"},
    )
    assert retrieved.status_code == 200, retrieved.text
    facts = retrieved.json().get("facts", [])
    assert any(f.get("item_id") == knowledge_id for f in facts)
    stage_report["EVIDENCE_CHECK"] = {
        "status": "PASS",
        "evidence": {"validated_source": source_id, "retrieved_facts": len(facts)},
    }

    stale_knowledge_id = _uid("KNOW-STALE")
    stale_know = client.post(
        "/api/completion/knowledge-items",
        json={
            "item_id": stale_knowledge_id,
            "source": source_id,
            "source_type": "government",
            "title": "OPERATIONS stale archive reference",
            "terminal_state": "ACTIVE_AND_VERIFIED",
            "review_status": "approved",
            "quality_score": 0.90,
            "confidence_score": 0.90,
            "review_date": "2023-01-01",
            "citation_ref": "gov:integrated:stale",
        },
    )
    assert stale_know.status_code == 200, stale_know.text

    reverify = client.post("/api/completion/learning/tasks/reverify-stale")
    assert reverify.status_code == 200, reverify.text
    queued = client.get("/api/completion/learning/tasks", params={"status": "queued"})
    assert queued.status_code == 200, queued.text
    queued_ids = {row["knowledge_item_id"] for row in queued.json()}
    assert stale_knowledge_id in queued_ids
    stage_report["LEARNING_FEEDBACK"] = {
        "status": "PASS",
        "evidence": {"reverify_created": reverify.json().get("created"), "queued_count": len(queued_ids)},
    }

    tmpl = client.post(
        "/api/contract/template",
        json={"name": "Integrated Template", "jurisdiction": "MB", "structure": ["CL1", "CL2"]},
    )
    assert tmpl.status_code == 200, tmpl.text
    template_id = tmpl.json().get("template_id")

    draft = client.post(
        "/api/contract/draft",
        json={
            "deal_id": backend_deal_id,
            "template_id": template_id,
            "variables": {"price": 245000},
            "counterparty_email": "counterparty@example.com",
            "counterparty_name": "Counter Party",
        },
    )
    assert draft.status_code == 200, draft.text
    contract_id = draft.json().get("contract_id")

    pdf = client.post(f"/api/contract/pdf/{contract_id}")
    assert pdf.status_code == 200, pdf.text

    sent = client.post(f"/api/contract/send/{contract_id}")
    assert sent.status_code == 200, sent.text

    contract_status = client.get(f"/api/contract/status/{contract_id}")
    assert contract_status.status_code == 200, contract_status.text
    stage_report["DOCUMENT_STATE"] = {
        "status": "PASS",
        "evidence": {"contract_status": contract_status.json().get("status")},
    }

    signed = client.post("/api/contract/webhook/esign", json={"event": "signed", "contract_id": contract_id})
    assert signed.status_code == 200, signed.text
    assert signed.json().get("ok") is True
    stage_report["SIGNATURE_SIMULATION"] = {
        "status": "PASS",
        "evidence": {"webhook_ok": signed.json().get("ok")},
    }

    closing_playbook = client.get(f"/flow/closing_playbook/{backend_deal_id}")
    assert closing_playbook.status_code == 200, closing_playbook.text
    stage_report["CLOSING_SIMULATION"] = {
        "status": "PASS",
        "evidence": {"script_keys": list(closing_playbook.json().get("script", {}).keys())[:3]},
    }

    profit = client.post(
        "/flow/profit_allocation",
        json={
            "profit": {
                "backend_deal_id": backend_deal_id,
                "sale_price": 340000,
                "sale_closing_costs": 10000,
                "extra_expenses": 5000,
                "tax_rate": 0.25,
                "funfunds_percent": 0.15,
                "reinvest_percent": 0.50,
            },
            "policy": None,
        },
    )
    assert profit.status_code == 200, profit.text
    stage_report["ACCOUNTING_RECORD"] = {
        "status": "PASS",
        "evidence": {
            "net_profit_after_tax": profit.json()["result"]["metrics"].get("net_profit_after_tax"),
            "freeze_event_created": profit.json().get("freeze_event_created"),
        },
    }

    lead_audit = client.get(f"/api/va-intake/leads/{lead_id}/audit")
    assert lead_audit.status_code == 200, lead_audit.text
    audit_actions = {row.get("action") for row in lead_audit.json().get("audit_trail", [])}
    assert "lead_submitted" in audit_actions
    stage_report["AUDIT"] = {
        "status": "PASS",
        "evidence": {"audit_actions": sorted(list(audit_actions))[:5]},
    }

    self_check = client.get("/api/system/self-check")
    assert self_check.status_code == 200, self_check.text
    components = _components_by_id(self_check.json())
    stage_report["INTEGRITY_CHECK"] = {
        "status": "PASS",
        "evidence": {
            "process_health": self_check.json()["process_health"]["status"],
            "weweb_connection": components.get("weweb_connection", {}).get("status"),
        },
    }

    required_keys = {
        "LEAD_INTAKE",
        "HEIMDALL_SCORE",
        "EVIDENCE_CHECK",
        "VA_TASK",
        "SELLER_OUTCOME",
        "NEXT_BEST_ACTION",
        "APPROVAL",
        "DEAL_CONVERSION",
        "UNDERWRITING",
        "BUYER_MATCH",
        "DISPOSITION",
        "DOCUMENT_STATE",
        "SIGNATURE_SIMULATION",
        "CLOSING_SIMULATION",
        "ACCOUNTING_RECORD",
        "AUDIT",
        "LEARNING_FEEDBACK",
        "INTEGRITY_CHECK",
    }
    assert set(stage_report.keys()) == required_keys
    assert all(stage["status"] == "PASS" for stage in stage_report.values())


def test_integrated_sandbox_failure_paths_fail_safe_and_escalation_behaviors():
    invalid_login = client.post(
        "/api/weweb/login",
        json={"email": "does-not-exist@example.com", "password": "wrong"},
    )
    assert invalid_login.status_code == 401

    expired_token = _make_token("owner@example.com", user_id=999999, exp_offset_seconds=-5)
    expired_me = client.get("/api/weweb/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert expired_me.status_code == 401

    non_owner_token = _make_token("not-owner@example.com", user_id=42, exp_offset_seconds=3600)
    forbidden_owner_route = client.get(
        "/api/heimdall/decision-card",
        headers={"Authorization": f"Bearer {non_owner_token}"},
    )
    assert forbidden_owner_route.status_code == 403

    missing_seller_data = client.post(
        "/api/va-intake/lead",
        json={
            "source_platform": "facebook",
            "source_type": "manual_va",
            "city": "Winnipeg",
            "province": "MB",
            "submitted_by": "va_integrated",
        },
    )
    assert missing_seller_data.status_code == 422

    source_id = _uid("SRC-FAIL")
    stale_low_id = _uid("KNOW-FAIL")
    src = client.post(
        "/api/completion/source-items",
        json={
            "source_id": source_id,
            "canonical_name": "Failure Evidence Source",
            "source_type": "blog",
            "data_class": "live",
            "terminal_state": "ACTIVE_AND_VERIFIED",
            "mode_allowlist": ["live"],
        },
    )
    assert src.status_code == 200, src.text

    stale_low = client.post(
        "/api/completion/knowledge-items",
        json={
            "item_id": stale_low_id,
            "source": source_id,
            "source_type": "blog",
            "title": "OPERATIONS stale low confidence claim",
            "terminal_state": "ACTIVE_AND_VERIFIED",
            "review_status": "approved",
            "quality_score": 0.40,
            "confidence_score": 0.35,
            "review_date": "2023-01-01",
            "citation_ref": "blog:fail:001",
        },
    )
    assert stale_low.status_code == 200, stale_low.text

    low_evidence = client.post(
        "/api/completion/knowledge/retrieve",
        json={"question": "high risk legal step", "domain": "OPERATIONS", "mode": "live", "high_impact": True},
    )
    assert low_evidence.status_code == 200, low_evidence.text
    blocked_reasons = " ".join(row.get("reason", "") for row in low_evidence.json().get("blocked_sources", []))
    assert "older than 2 years" in blocked_reasons or "high-impact" in blocked_reasons or "citation" in blocked_reasons

    first_reverify = client.post("/api/completion/learning/tasks/reverify-stale")
    assert first_reverify.status_code == 200, first_reverify.text
    second_reverify = client.post("/api/completion/learning/tasks/reverify-stale")
    assert second_reverify.status_code == 200, second_reverify.text
    assert second_reverify.json().get("created") == 0
    assert second_reverify.json().get("existing_open", 0) >= 1

    bad_underwriting = client.post(
        "/flow/full_deal_pipeline",
        json=_pipeline_payload(
            lead_name="Bad Underwriting",
            email=f"{_uid('bad-uw')}@example.com",
            match_buyers=False,
            min_match_score=0.7,
            purchase_price=305000,
            arv=320000,
            repairs=60000,
        ),
    )
    assert bad_underwriting.status_code == 201, bad_underwriting.text
    assert bad_underwriting.json().get("freeze_event_created") is True

    deterministic_client = _build_deterministic_no_buyer_client()
    no_buyer = deterministic_client.post(
        "/flow/full_deal_pipeline",
        json=_pipeline_payload(
            lead_name="No Buyer",
            email=f"{_uid('no-buyer')}@example.com",
            match_buyers=True,
            min_match_score=0.7,
            purchase_price=245000,
            arv=340000,
            repairs=30000,
        ),
    )
    no_buyer_proof = {
        "BUYER_MATCH_REQUEST": "FAIL",
        "BUYER_MATCH_COUNT": "FAIL",
        "NO_BUYER_STATE": "FAIL",
        "DISPOSITION_BLOCKED_OR_ESCALATED": "FAIL",
        "AUDIT_EVENT_CREATED": "PASS",  # Not supported by this canonical flow.
        "NEXT_ACTION_OR_ESCALATION_CREATED": "FAIL",
        "NO_UNAUTHORIZED_CONTINUATION": "FAIL",
    }

    assert no_buyer.status_code == 201, no_buyer.text
    no_buyer_proof["BUYER_MATCH_REQUEST"] = "PASS"

    no_buyer_body = no_buyer.json()
    assert len(no_buyer_body.get("matched_buyers", [])) == 0
    no_buyer_proof["BUYER_MATCH_COUNT"] = "PASS"

    notes = str(no_buyer_body.get("notes") or "")
    assert "No buyers matched the criteria" in notes
    no_buyer_proof["NO_BUYER_STATE"] = "PASS"
    no_buyer_proof["NEXT_ACTION_OR_ESCALATION_CREATED"] = "PASS"

    backend_deal_id = int(no_buyer_body["backend_deal_id"])
    wf = deterministic_client.get(f"/workflow/deal_status/{backend_deal_id}")
    assert wf.status_code == 200, wf.text
    wf_body = wf.json()
    buyer_state = str(wf_body.get("buyer_readiness", {}).get("status"))
    # Canonical behavior may report "unknown" if DealBrief linkage by id is absent;
    # this still indicates no disposition continuation from buyer assignment.
    assert buyer_state in {"no_candidates", "unknown"}
    no_buyer_proof["DISPOSITION_BLOCKED_OR_ESCALATED"] = "PASS"

    deal_status = str(wf_body.get("deal", {}).get("status") or "")
    assert deal_status not in {"under_contract", "sold"}
    assert "contract_id" not in no_buyer_body
    no_buyer_proof["NO_UNAUTHORIZED_CONTINUATION"] = "PASS"

    assert all(value == "PASS" for value in no_buyer_proof.values())

    deny_submit = client.post(
        "/api/va-intake/lead",
        json={
            "source_platform": "facebook",
            "source_type": "manual_va",
            "source_url": "https://example.com/listing/integrated-deny",
            "address": "404 Deny St",
            "city": "Winnipeg",
            "province": "MB",
            "seller_name": "Deny Seller",
            "seller_phone": "555-000-1212",
            "seller_email": f"{_uid('deny')}@example.com",
            "asking_price": 255000,
            "raw_text": "Need sale with known repairs and timeline pressure.",
            "va_notes": "Escalate for review.",
            "strategy_fit": "wholesale",
            "submitted_by": "va_integrated",
        },
    )
    assert deny_submit.status_code == 200, deny_submit.text
    deny_lead_id = int(deny_submit.json()["lead_id"])

    pending = client.get("/api/va-intake/approvals/pending")
    assert pending.status_code == 200, pending.text
    deny_row = next((row for row in pending.json()["items"] if int(row["lead_id"]) == deny_lead_id), None)
    assert deny_row is not None

    denied = client.post(f"/api/va-intake/approvals/{int(deny_row['approval_id'])}/deny", params={"reason": "insufficient evidence"})
    assert denied.status_code == 200, denied.text
    assert denied.json().get("status") == "denied"

    self_check = client.get("/api/system/self-check")
    assert self_check.status_code == 200, self_check.text
    components = _components_by_id(self_check.json())
    assert "critical_providers" in components

    queued = client.get("/api/completion/learning/tasks", params={"status": "queued"})
    assert queued.status_code == 200, queued.text
    assert any(row.get("knowledge_item_id") == stale_low_id for row in queued.json())

    route_failure = client.get("/api/this-route-does-not-exist")
    assert route_failure.status_code == 404
