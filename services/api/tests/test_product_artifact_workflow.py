import base64
import hashlib
import json
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.god.models import GodReviewCase, GodReviewEvent
from app.loki.models import LokiFinding, LokiIndependentReceipt, LokiReconsideration, LokiReview
from app.models.god_verdicts import GodVerdict
from app.models.governance_decision import GovernanceDecision
from app.models.completion_registry import (
    KnowledgeRegistryItem, LearningFeedbackRecord, LearningTaskQueueItem, LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent, SourceRegistryItem,
)
from app.models.media_engine import MediaContent
from app.models.foundry_checkout import FoundryCampaignVisit, FoundryFixtureSettlement, FoundryRehearsalOrder, FoundryRehearsalPayment
from app.models.marketing import MarketingCampaign
from app.models.audit_log import AuditLog
from app.models.go_live_state import GoLiveState
from app.models.revenue_ledger import RevenueLedger
from app.models.owner_conversation import OwnerConversation, OwnerTurn
from app.models.product_artifact import ProductArtifact
from app.models.prime_specialist_schedule import PrimeScheduleTrigger, PrimeSpecialistSchedule
from app.models.specialist_assignment import SpecialistAssignment, SpecialistTrigger
from app.pantheon.monitor import run_assignment
from app.routers.prime_specialist_schedules import _utc_now, run_due_schedule


FACTORY = "/api/business-factory"
ASSETS = f"{FACTORY}/product-artifacts"
PHASE3 = "/api/completion/phase3/universal-opportunity"


def test_internal_product_asset_stage_bind_verify_and_revoke(deal_client, monkeypatch):
    client, engine = deal_client
    admin = {"X-Business-Factory-Key": "ci-factory-for-product-assets"}
    owner = {**admin, "X-Owner-Mandate-Key": "ci-owner-for-product-assets"}
    monkeypatch.setenv("VALHALLA_FACTORY_KEY", admin["X-Business-Factory-Key"])
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", owner["X-Owner-Mandate-Key"])
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    for model in (LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent, MediaContent):
        model.__table__.create(engine)

    scope = {"legacy_instance_id": "legacy-north", "business_id": "workshop", "engine_id": "micro_saas", "jurisdiction": "CA-MB"}
    with Session(engine) as db:
        db.add(LegacyInstanceRegistryItem(
            legacy_instance_id=scope["legacy_instance_id"], display_name="Internal operating legacy",
            assigned_businesses_json='["workshop"]', assigned_jurisdictions_json='["CA-MB"]', engines_json='["micro_saas", "market_intelligence"]',
            local_knowledge_context_json='{"business_id":"workshop","jurisdiction":"CA-MB"}',
            synchronization_status="SYNCED", status="PASS",
        ))
        db.commit()

    content = b"Valhalla owns this product test file.\n"
    checksum = hashlib.sha256(content).hexdigest()
    asset_id = str(uuid4())
    asset = {
        **scope, "artifact_id": asset_id, "product_id": "workshop-guide", "version": 1,
        "media_type": "text/plain", "sha256": checksum,
        "content_base64": base64.b64encode(content).decode(), "rights_reference": "internal-rights-register/example-001",
        "attestation": "OWNER_AUTHORIZES_INTERNAL_STORAGE_AND_USE",
    }

    assert client.post(ASSETS, headers=owner, json=asset).status_code == 503
    ProductArtifact.__table__.create(engine)
    assert client.post(ASSETS, headers=admin, json=asset).status_code == 401
    assert client.post(ASSETS, headers=owner, content=b"x" * (7 * 1024 * 1024 + 1)).status_code == 413
    assert client.post(ASSETS, headers=owner, json={**asset, "sha256": "0" * 64}).status_code == 422
    assert client.post(ASSETS, headers=owner, json={**asset, "media_type": "application/pdf"}).status_code == 422
    assert client.post(ASSETS, headers=owner, json={**asset, "jurisdiction": "CA-ON"}).status_code == 409

    staged = client.post(ASSETS, headers=owner, json=asset)
    assert staged.status_code == 201, staged.text
    assert staged.json()["rights_basis"] == "OWNER_ATTESTED_INTERNAL_USE"
    assert staged.json()["external_delivery_authorized"] is False
    assert client.post(ASSETS, headers=owner, json=asset).json() == staged.json()
    assert client.post(ASSETS, headers=owner, json={**asset, "artifact_id": str(uuid4())}).status_code == 409

    download_url = f"{ASSETS}/{asset_id}/download"
    assert client.get(download_url, headers=admin).status_code == 401
    download = client.get(download_url, headers=owner)
    assert download.content == content
    assert download.headers["X-Artifact-SHA256"] == checksum

    listing = {
        **scope, "artifact_id": asset_id, "product_id": asset["product_id"], "industry": "digital products",
        "title": "Workshop operations guide", "description": "An internal preview of the workshop operations guide and checklist.",
        "price_cents_cad": 2500, "request_key": "workshop-listing-01",
    }
    assert client.post(f"{FACTORY}/listing-drafts", headers=admin, json={**listing, "product_id": "other-product"}).status_code == 409

    def submit_and_approve(body):
        accepted = client.post(f"{FACTORY}/listing-drafts", headers=admin, json=body)
        assert accepted.status_code == 200, accepted.text
        action_id = accepted.json()["action_id"]
        approved = client.post(
            f"{FACTORY}/actions/{action_id}/approve", headers=owner, json={"confirmation": "APPROVE_INTERNAL_DRAFT"},
        )
        assert approved.status_code == 200, approved.text
        return action_id

    for model in (GodReviewCase, GodReviewEvent, GodVerdict, GovernanceDecision, LokiReview,
                  LokiFinding, LokiIndependentReceipt, LokiReconsideration):
        model.__table__.create(engine)

    worker = {"X-Loki-Reviewer-Key": "independent-product-test-reviewer"}
    monkeypatch.setenv("VALHALLA_LOKI_REVIEWER_KEY", worker["X-Loki-Reviewer-Key"])
    monkeypatch.setenv("VALHALLA_LOKI_REVIEWER_ID", "independent-product-review")
    proposal = {
        "opportunity_id": "product-development-001", "engine_id": scope["engine_id"], "legacy": scope["legacy_instance_id"],
        "jurisdiction": scope["jurisdiction"], "title": listing["title"], "summary": listing["description"],
        "evidence_confidence": 0.95, "strategic_value": 0.9, "downside_exposure": 0.1, "blast_radius": "LOW",
        "required_capital": 1000, "maximum_capital_exposure": 1000, "required_reserve_to_survive_failure": 100,
        "available_safe_capital": 1000, "point_of_no_return": "External publication or paid access",
        "exit_options": ["Archive the private preview before any publication"],
        "specialist_inputs": {
            "business_id": scope["business_id"],
            "proposed_internal_listing": {
                **{key: listing[key] for key in (
                    "artifact_id", "product_id", "industry", "title", "description", "price_cents_cad",
                )},
                "artifact_sha256": checksum,
            },
            **dict.fromkeys(("niche_demand", "addressable_niche", "pricing_power", "retention", "defensibility", "global_reach"), 0.95),
            **dict.fromkeys(("churn_risk", "technical_build_effort", "hosting_api_cost", "support_burden"), 0.05),
        },
    }
    for model in (KnowledgeRegistryItem, SourceRegistryItem, LearningFeedbackRecord, PrimeSpecialistSchedule, PrimeScheduleTrigger, OwnerConversation, OwnerTurn, SpecialistAssignment, SpecialistTrigger):
        model.__table__.create(engine)
    from app.models.economic_control import EconomicOperation, EconomicPool, EconomicRecord
    from app.models.foundry_evidence import FoundryEvidence
    from app.models.foundry_intake import FoundryIntakeJob
    from app.services import foundry_intake
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    for model in (FoundryEvidence, FoundryIntakeJob, EconomicPool, EconomicOperation, EconomicRecord):
        model.__table__.create(engine)

    at = foundry_intake.current_time()
    today = at.date()
    previous_day = today - timedelta(days=1)
    economy = "/api/prime/economy"

    def economic(path, body, expected=201):
        response = client.post(f"{economy}/{path}", json=body, headers=owner)
        assert response.status_code == expected, response.text
        return response.json()

    with Session(engine) as db:
        db.add(EconomicPool(currency="CAD"))
        db.add(SourceRegistryItem(source_id="workshop-demand-fixture", source_type="DEMAND_EXPORT",
                                  canonical_name="Isolated signed workshop survey", data_class="live",
                                  jurisdiction=scope["jurisdiction"], terminal_state="PASS",
                                  mode_allowlist_json='["practice"]', freshness_sla_hours=72))
        db.commit()

    def enroll(role):
        response = client.post("/api/prime/pantheon/assignments", headers=owner, json={
            **scope, "assignment_id": str(uuid4()), "role": role, "cadence_seconds": 600, "duration_seconds": 7200,
        })
        assert response.status_code == 201, response.text

    enroll("ODIN")
    key = Ed25519PrivateKey.generate()
    intake = "/api/prime/foundry/intake"
    source = "workshop-demand-fixture"
    assert client.put(f"{intake}/sources/{source}/signing-key", headers=owner, json={
        "public_key_hex": key.public_key().public_bytes_raw().hex(),
    }).status_code == 200
    evidence_id = str(uuid4())
    export = {
        "source_id": source, "external_key": "workshop-survey", "adapter": "DEMAND_EXPORT",
        "buyer_segment": "Practice workshop operators", "sample_count": 20, "demand_count": 15,
        "source_signed_at": at.isoformat() + "Z",
        "evidence": {**scope, "evidence_id": evidence_id, "kind": "DIGITAL_PRODUCT",
                     "evidence_class": "OPERATOR_REPORTED", "title": listing["title"], "source_ref": "fixture:survey",
                     "observed_on": today.isoformat(), "expires_on": (today + timedelta(days=2)).isoformat(),
                     "currency": "CAD", "unit_price": 2500, "variable_cost_per_unit": 175,
                     "acquisition_cost_per_unit": 0, "monthly_fixed_cost": 0, "monthly_units": 4,
                     "startup_capital": 500, "test_cost": 100,
                     "rights_attestation": "AUTHORIZED_INTERNAL_RESEARCH"},
    }
    export["source_signature"] = key.sign(foundry_intake.source_signature_message(export)).hex()
    received = client.post(intake, json=export, headers=owner)
    assert received.status_code == 202, received.text
    with Session(engine) as db:
        tick = foundry_intake.current_time()
        assert foundry_intake.run_intake(db, now=tick)["status"] == "COMPLETED"
        specialist_report_id = run_assignment(db, "ODIN", now=tick)["report_event_id"]
    source_report = client.get(f"/api/prime/pantheon/reports/{specialist_report_id}").json()
    assert source_report["trigger"] == "SOURCE_DISCOVERY"
    candidate = client.get(f"/api/prime/foundry/reports/{specialist_report_id}/candidate/{evidence_id}")
    assert candidate.status_code == 200, candidate.text
    grounded = candidate.json()["proposal"]
    proposal = {**proposal, **grounded, "persist_decision": True,
                "specialist_inputs": {**proposal["specialist_inputs"], **grounded["specialist_inputs"]}}
    assert proposal["specialist_inputs"]["discovery_demand"]["sample_demand_bp"] == 7500

    capital_mandate = {"id": str(uuid4()), "scope": scope, "currency": "CAD", "max_exposure": 5000,
               "max_cumulative_loss": 175, "max_additional_funding": 1000, "min_operating_reserve": 200,
               "review_by": (today + timedelta(days=10)).isoformat(), "minimum_period_net": 0,
               "continuation_criteria": "Preserve positive fixture unit economics.",
               "suspension_criteria": "Contain at the fixture loss limit.",
               "exit_criteria": "Archive failed demand experiments.", "obligations": ["Review fixture receipts"]}
    economic("mandates", capital_mandate)
    performance = {"id": str(uuid4()), "scope": scope, "start": previous_day.isoformat(),
                   "end": previous_day.isoformat(), "operating_receipts": 200, "operating_costs": 50,
                   "outstanding_exposure": 0, "uncommitted_local_cash": 2000,
                   "receipt_ref": "fixture:prior-workshop-evidence", "obligations_status": "SATISFIED",
                   "evidence_class": "RECONCILIATION_FIXTURE"}
    economic("performance", performance)
    economic("liquidity", {"id": str(uuid4()), "scope": scope, "receipt_ref": "fixture:startup-capital",
                           "as_of": today.isoformat(), "unrestricted_pool_minor": 2000,
                           "protected_pool_minor": 8000, "evidence_class": "RECONCILIATION_FIXTURE"})
    schedule_root = "/api/prime/specialist-schedules"
    schedule_id = str(uuid4())
    other_schedule_id = str(uuid4())
    schedule = {
        "schedule_id": schedule_id, "cadence_seconds": 3600, "duration_seconds": 7200,
        "on_verified_outcome": True, "opportunity": proposal, "business_id": scope["business_id"],
    }
    for configuration in (schedule, {
        **schedule, "schedule_id": other_schedule_id,
        "opportunity": {**proposal, "engine_id": "market_intelligence"},
    }):
        created = client.post(schedule_root, headers=owner, json=configuration)
        assert created.status_code == 201, created.text
    slot_time = _utc_now() + timedelta(seconds=1)
    for _ in range(2):
        with Session(engine) as db:
            assert run_due_schedule(db, now=slot_time)["status"] == "evaluated"
    cid = str(uuid4())
    threads = "/api/jarvis/conversations"
    assert client.post(threads, json={"conversation_id": cid, "title": "Private operating rehearsal"}).status_code == 201
    turns = f"{threads}/{cid}/turns"

    def owner_turn(message, **context):
        result = client.post(turns, json={"turn_id": str(uuid4()), "message": message, **context})
        assert result.status_code == 201, result.text
        return result.json()

    with Session(engine) as db:
        db.add(SourceRegistryItem(
            source_id="rehearsal-source", canonical_name="Isolated source fixture", source_type="government",
            data_class="live", jurisdiction=scope["jurisdiction"], terminal_state="ACTIVE_AND_VERIFIED",
        ))
        db.add(KnowledgeRegistryItem(
            item_id="rehearsal-publisher-policy", source="rehearsal-source", title="Workshop permission reference",
            source_type="government", jurisdiction=scope["jurisdiction"], terminal_state="ACTIVE_AND_VERIFIED",
            review_status="approved", review_date=_utc_now().date(), allowed_systems_json='["Heimdall"]',
            citation_ref="fixture:internal-workshop-rights", quality_score=0.95, confidence_score=0.95,
        ))
        db.commit()
    research = owner_turn("Find the source for this review", knowledge_domain="Workshop", knowledge_jurisdiction=scope["jurisdiction"])
    assert research["evidence"]["knowledge"]["facts"][0]["item_id"] == "rehearsal-publisher-policy"
    first = owner_turn("Review the product specialist report", specialist_schedule_id=schedule_id)
    assert first["evidence"]["evidence_class"] == "INTERNAL_ADVISORY"
    assert first["evidence"]["verified_internal_outcome_ids"] == []
    next_cadence = client.get(f"{schedule_root}/{schedule_id}").json()["next_due_at"]
    unrelated_advice = client.get(f"{schedule_root}/{other_schedule_id}").json()["latest_report"]

    assert client.post(f"{FACTORY}/listing-drafts", headers=admin, json={
        **listing, "prime_verdict_id": str(uuid4()),
    }).status_code == 409
    enroll("MIMIR")
    challenged = client.post(f"/api/prime/pantheon/reports/{specialist_report_id}/challenge")
    assert challenged.status_code == 201, challenged.text
    report_review = challenged.json()
    proposal["specialist_inputs"]["pantheon_report_ids"] = [specialist_report_id]
    artifact = client.post(f"{PHASE3}/review-artifact", json=proposal).json()
    queued = client.post("/loki/reviews", json={**artifact, "input_source": "prime-product-rehearsal"})
    assert queued.status_code == 201, queued.text
    review_id = queued.json()["id"]
    review = client.get("/loki/worker/reviews", params={"artifact_type": "universal_opportunity"}, headers=worker).json()[0]
    assert review["raw_input"]["specialist_inputs"]["proposed_internal_listing"]["artifact_sha256"] == checksum
    finding = {
        "artifact_sha256": review["artifact_sha256"], "analysis_ref": "fixture:dry-run/product-rights",
        "summary": "Check that the stated permission covers internal testing only.",
        "findings": [{
            "category": "license_scope", "severity": "warn", "material": True,
            "message": "Restrict this action to reversible internal testing.", "evidence_ref": "fixture:owner-attestation",
        }],
    }
    result = client.post(f"/loki/worker/reviews/{review_id}/result", headers=worker, json=finding)
    assert result.status_code == 201, result.text

    def evaluate():
        return client.post(f"{PHASE3}/evaluate", json={
            "shadow_mode": False,
            "opportunities": [{**proposal, "independent_loki_review_id": review_id}],
        })

    assert evaluate().status_code == 409
    findings = client.get(f"/loki/reviews/{review_id}/findings").json()
    reconsider = client.post(f"/loki/reviews/{review_id}/reconsider", headers=owner, json={
        "artifact_sha256": review["artifact_sha256"], "disposition": "accept_risk",
        "material_finding_ids": [findings[0]["id"]],
        "reason": "Owner confirms that reversible private testing stays within the internal attestation.",
    })
    assert reconsider.status_code == 200, reconsider.text
    assert evaluate().status_code == 409
    from app.loki.analyst import challenge

    specialist_queue = client.get("/loki/worker/reviews", params={"artifact_type": "pantheon_report"}, headers=worker)
    specialist_input = specialist_queue.json()[0]
    specialist_result = challenge(specialist_input).model_dump(mode="json")
    specialist_path = f"/loki/reviews/{report_review['review_id']}"
    published = client.post(f"/loki/worker/reviews/{report_review['review_id']}/result", headers=worker, json=specialist_result)
    assert published.status_code == 201, published.text
    assert evaluate().status_code == 409
    specialist_findings = client.get(f"{specialist_path}/findings").json()
    acknowledged = client.post(f"{specialist_path}/reconsider", headers=owner, json={
        "artifact_sha256": report_review["artifact_sha256"], "disposition": "accept_risk",
        "material_finding_ids": [item["id"] for item in specialist_findings],
        "reason": "Rechecked source references within the authorized workshop rehearsal.",
    })
    assert acknowledged.status_code == 200, acknowledged.text
    decision = evaluate()
    assert decision.status_code == 200, decision.text
    advice = decision.json()["evaluations"][0]
    assert advice["final_decision"] in {"proceed", "research_more"}, advice["final_decision"]
    assert advice["capital_risk_exit_analysis"]["hard_decision_rule_pass"], advice["hard_gate_evaluation"]
    listing["prime_verdict_id"] = advice["persistence"]["god_verdict_id"]
    decision_turn = owner_turn("Show the independently reviewed recommendation", prime_decision_id=listing["prime_verdict_id"])
    assert decision_turn["evidence"]["independent_loki"]["review_id"] == review_id
    assert decision_turn["evidence"]["independent_loki"]["reconsideration_status"] == "accept_risk"
    assert decision_turn["execution_authorized"] is False
    different_price = client.post(f"{FACTORY}/listing-drafts", headers=admin, json={
        **listing, "price_cents_cad": listing["price_cents_cad"] + 1,
    })
    assert different_price.status_code == 409, different_price.text

    mandate = {
        **scope, "product_id": asset["product_id"], "mandate_id": "product-rehearsal-mandate",
        "ttl_seconds": 600, "max_uses": 1, "max_price_cents_cad": listing["price_cents_cad"],
    }
    granted = client.post(f"{FACTORY}/mandates", headers=owner, json=mandate)
    assert granted.status_code == 200, granted.text
    assigned = client.post(f"{FACTORY}/listing-drafts", headers=admin, json={
        **listing, "mandate_id": mandate["mandate_id"],
    })
    assert assigned.status_code == 200, assigned.text
    action_id = assigned.json()["action_id"]
    from app.models.norns_forecast import NornsForecast, NornsHoldout

    for model in (NornsForecast, NornsHoldout):
        model.__table__.create(engine)
    forecast_id = str(uuid4())
    forecast = client.post("/api/prime/norns/forecasts", headers=owner, json={
        "forecast_id": forecast_id, "action_id": action_id, "probability_bp": 8000, "horizon_seconds": 120,
    })
    assert forecast.status_code == 201, forecast.text
    approved_capital = economic("assessment", scope, 200)
    assert approved_capital["period_net_minor"] == 150 and approved_capital["new_exposure_available_minor"] >= 500
    executed = client.post(f"{FACTORY}/actions/run-once", headers=admin).json()
    assert executed["status"] == "completed"
    assert executed["receipt"]["sales_verified"] is False
    assert executed["receipt"]["authority_mode"] == "STANDING_MANDATE"
    assert executed["receipt"]["product_asset"]["sha256"] == checksum
    assert executed["receipt"]["prime_decision"]["review_id"] == review_id
    assert executed["receipt"]["prime_decision"]["reviewed_specialist_reports"][0]["review_id"] == report_review["review_id"]
    assert executed["receipt"]["prime_decision"]["verdict_id"] == listing["prime_verdict_id"]
    with Session(engine) as db:
        listing_record = db.get(MediaContent, executed["receipt"]["media_content_id"])
        assert json.loads(listing_record.body)["product_asset"]["sha256"] == checksum
        assert json.loads(listing_record.body)["purchase_url"] is None
    assert client.get(f"{FACTORY}/actions/{action_id}", headers=admin).json()["internal_artifact_verified"]
    resolved = client.post(f"/api/prime/norns/forecasts/{forecast_id}/resolve")
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["observed_outcome"] == 1
    assert resolved.json()["evidence_ref"].startswith("BF-RECEIPT-")
    closed_order = rehearse_checkout(client, engine, monkeypatch, owner, action_id, listing["price_cents_cad"], scope)
    pending_id = submit_and_approve({**listing, "request_key": "workshop-listing-02"})
    with Session(engine) as db:
        advanced = run_assignment(db, "ODIN")
        assert advanced["report_event_id"] != specialist_report_id
    stale = client.post(f"{FACTORY}/actions/run-once", headers=admin).json()
    assert stale["action_id"] == pending_id and "stale" in stale["reason"]
    with Session(engine) as db:
        db.get(ProductArtifact, UUID(asset_id)).data = b"Bad storage bytes"
        db.commit()
    assert client.get(download_url, headers=owner).status_code == 409
    blocked = client.post(f"{FACTORY}/actions/run-once", headers=admin).json()
    assert blocked["action_id"] == pending_id
    assert blocked["reason"] == "Internal product artifact integrity mismatch"
    with Session(engine) as db:
        db.get(ProductArtifact, UUID(asset_id)).data = content
        db.commit()

    adverse = {**performance, "id": str(uuid4()), "start": today.isoformat(), "end": today.isoformat(),
               "operating_receipts": closed_order["net_minor"], "operating_costs": closed_order["fixture_cost_minor"],
               "receipt_ref": f"fixture:checkout-{closed_order['order_id']}"}
    economic("performance", adverse)
    economic("mandates", {**capital_mandate, "id": str(uuid4()), "previous_id": capital_mandate["id"]})
    after = economic("assessment", scope, 200)
    assert after["period_net_minor"] == -175 and after["cumulative_loss_minor"] == 175
    assert after["suggested_action"] == "EXIT"

    with Session(engine) as db:
        triggered = run_due_schedule(db, now=slot_time + timedelta(seconds=1))
        assert triggered["status"] == "evaluated"
    advice = client.get(f"{schedule_root}/{schedule_id}").json()
    assert advice["next_due_at"] == next_cadence
    report = advice["latest_report"]
    assert report["trigger"] == "VERIFIED_OUTCOME"
    assert report["trigger_outcome_event_id"] == report["verified_internal_outcomes"][0]["outcome_event_id"]
    assert report["verified_internal_outcomes"][0]["prime_decision"]["verdict_id"] == listing["prime_verdict_id"]
    assert report["verified_internal_outcomes"][0]["sales_verified"] is False
    reassessment = report["operating_reassessment"]
    [learning] = reassessment["checkout_learning"]
    assert learning["status"] == "MATCHED_FIXTURE" and learning["fixture_contribution_minor"] == -175
    assert len(learning["matched_fixture_payment_ids"]) == 3
    assert reassessment["economic_reassessment"]["cumulative_loss_minor"] == 175
    assert {"NEGATIVE_FIXTURE_CONTRIBUTION", "CUMULATIVE_LOSS_LIMIT"} <= set(reassessment["blockers"])
    assert report["recommendation"]["heimdall_decision"] == "HOLD"
    assert first["evidence"]["heimdall_decision"] != report["recommendation"]["heimdall_decision"]
    assert report["recommendation"]["abstain"]
    follow_up = owner_turn("What did we learn after the internal draft?", specialist_schedule_id=schedule_id)
    assert follow_up["evidence"]["operating_reassessment"] == reassessment
    assert follow_up["evidence"]["verified_internal_outcome_ids"] == [report["trigger_outcome_event_id"]]
    assert len(client.get(turns).json()) == 4
    for model in (LearningTaskQueueItem, RevenueLedger, GoLiveState):
        model.__table__.create(engine)
    with Session(engine) as db:
        db.add(AuditLog(event_type="integrity_alert", event_source="rehearsal", message="Fixture recorded alert"))
        db.add(GoLiveState(id=1, go_live_enabled=False, kill_switch_engaged=False))
        db.add(RevenueLedger(engine_code="micro_saas", currency="CAD", gross_amount=50, as_of_date=date.today()))
        db.commit()
    brief = owner_turn("Morning briefing")["evidence"]["operating_evidence"]
    assert any(item["report_event_id"] == specialist_report_id for item in brief["latest_specialist_reports"])
    assert brief["loki"]["available"] is True
    assert brief["latest_integrity_alerts"][0]["source"] == "rehearsal"
    assert brief["financials"]["totals_by_currency"] == [{"currency": "CAD", "entries": 1, "recorded_gross": "50.00"}]
    assert brief["verified_cash_balance"] is None
    assert client.get(f"{schedule_root}/{other_schedule_id}").json()["latest_report"] == unrelated_advice
    with Session(engine) as db:
        assert run_due_schedule(db, now=slot_time + timedelta(seconds=1)) == {"status": "idle"}

    contained = client.post(f"{FACTORY}/actions/run-once", headers=admin).json()
    assert contained["action_id"] == pending_id
    assert "containment" in contained["reason"].lower()

    from app.routers import norns_forecasts

    denied_forecast = str(uuid4())
    forecast = client.post("/api/prime/norns/forecasts", headers=owner, json={
        "forecast_id": denied_forecast, "action_id": pending_id, "probability_bp": 3000, "horizon_seconds": 120,
    })
    assert forecast.status_code == 201, forecast.text
    later = norns_forecasts._now() + timedelta(minutes=3)
    monkeypatch.setattr(norns_forecasts, "_now", lambda: later)
    no_artifact = client.post(f"/api/prime/norns/forecasts/{denied_forecast}/resolve")
    assert no_artifact.status_code == 200, no_artifact.text
    assert no_artifact.json()["observed_outcome"] == 0
    assert client.get("/api/prime/norns/calibration").json()["brier_score"] == 0.065
    with Session(engine) as db:
        recent_mimir = run_assignment(db, "MIMIR")["report_event_id"]
    learned_response = client.get(f"/api/prime/pantheon/reports/{recent_mimir}").json()
    assert learned_response["observations"]["checkout_learning"][0]["fixture_contribution_minor"] == -175
    assert learned_response["observations"]["economic_reassessment"]["cumulative_loss_minor"] == 175
    next_tick = datetime.fromisoformat(next_cadence).replace(tzinfo=None) + timedelta(seconds=1)
    with Session(engine) as db:
        settlement = db.get(FoundryFixtureSettlement, "evt_fixture_capture")
        settlement.amount_minor += 1
        db.commit()
        assert run_due_schedule(db, now=next_tick)["status"] == "evaluated"
    contradicted = client.get(f"{schedule_root}/{schedule_id}").json()["latest_report"]
    assert "CHECKOUT_EVIDENCE_CONFLICT" in contradicted["operating_reassessment"]["blockers"]
    assert contradicted["operating_reassessment"]["economic_reassessment"]["cumulative_loss_minor"] == 175
    assert contradicted["recommendation"]["heimdall_decision"] == "HOLD"
    assert client.get(f"{schedule_root}/{schedule_id}/reports/{report['report_event_id']}").json() == report
    with Session(engine) as db:
        assert db.query(MediaContent).count() == 1
        learned = db.query(LegacyOrchestrationEvent).filter_by(event_type="MIMIR_INTERNAL_ARTIFACT_VERIFIED").one()
        verified = json.loads(learned.payload_json)
        assert verified["product_asset"]["sha256"] == checksum
        assert verified["prime_decision"]["proposal_sha256"] == artifact["artifact_sha256"]
    assert client.delete(f"{ASSETS}/{asset_id}", headers=admin).status_code == 401
    assert client.delete(f"{ASSETS}/{asset_id}", headers=owner).json()["revoked"]
    assert client.get(download_url, headers=owner).status_code == 409


def rehearse_checkout(client, engine, monkeypatch, owner, action_id, price, scope):
    import hmac
    import time

    for model in (MarketingCampaign, FoundryRehearsalOrder, FoundryRehearsalPayment, FoundryCampaignVisit):
        model.__table__.create(engine)
    secret = "fixture-test-secret"
    monkeypatch.setenv("VALHALLA_FOUNDRY_FIXTURE_SECRET", secret)
    root = "/api/prime/foundry/rehearsal"
    with Session(engine) as db:
        db.add(MarketingCampaign(id=1, name="Private rehearsal", strategy_payload="{}"))
        db.commit()
    visit_ids = [str(uuid4()), str(uuid4())]
    assert client.post(f"{root}/campaign-visits", json={**scope, "campaign_id": 1, "visit_id": visit_ids[0]}).status_code == 401
    for visit_id in visit_ids:
        visit = client.post(f"{root}/campaign-visits", headers=owner, json={**scope, "campaign_id": 1, "visit_id": visit_id})
        assert visit.status_code == 201, visit.text
    def summary():
        result = client.post(f"{root}/campaigns/1/summary", json=scope)
        assert result.status_code == 200, result.text
        return result.json()
    assert summary()["rehearsed_visits"] == 2
    assert summary()["rehearsed_conversions"] == 0
    order_id = str(uuid4())
    payment = "pi_fixture_verified_order"
    payload = {"order_id": order_id, "action_id": action_id, "payment_reference": payment, "visit_id": visit_ids[0]}
    assert client.post(f"{root}/orders", json=payload).status_code == 401
    created = client.post(f"{root}/orders", headers=owner, json=payload)
    assert created.status_code == 201, created.text
    assert created.json()["price_minor"] == price
    assert client.post(f"{root}/orders", headers=owner, json=payload).status_code == 201
    duplicate = {**payload, "order_id": str(uuid4()), "payment_reference": "pi_fixture_duplicate"}
    assert client.post(f"{root}/orders", headers=owner, json=duplicate).status_code == 409
    assert client.post(f"{root}/orders/{order_id}/delivery", headers=owner).status_code == 409

    def apply(kind, event_id, amount, *, live=False, valid=True):
        if kind == "payment_intent.succeeded":
            data = {"id": payment, "amount_received": amount}
        else:
            data = {"payment_intent": payment, "amount_refunded": amount}
        data["currency"] = "cad"
        body = json.dumps({"type": kind, "livemode": live, "id": event_id, "data": {"object": data}}).encode()
        timestamp = str(int(time.time()))
        digest = hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
        headers = {"Stripe-Signature": f"t={timestamp},v1={digest if valid else '0' * 64}"}
        return client.post(f"{root}/payment-fixtures", content=body, headers=headers)

    capture = "payment_intent.succeeded"
    refund = "charge.refunded"
    assert apply(refund, "evt_fixture_early_refund", 1).status_code == 409
    assert apply(capture, "evt_fixture_capture", price, live=True).status_code == 422
    assert apply(capture, "evt_fixture_capture", price, valid=False).status_code == 400
    assert apply(capture, "evt_fixture_capture", price + 5).status_code == 409
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    assert apply(capture, "evt_fixture_capture", price).status_code == 503
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    paid = apply(capture, "evt_fixture_capture", price)
    assert paid.status_code == 200, paid.text
    assert apply(capture, "evt_fixture_capture", price).json() == paid.json()
    assert summary()["rehearsed_conversions"] == 1
    assert summary()["rehearsed_net_minor"] == price
    assert apply(capture, "evt_fixture_capture", price + 5).status_code == 409
    delivered = client.post(f"{root}/orders/{order_id}/delivery", headers=owner)
    assert delivered.status_code == 200, delivered.text
    assert delivered.json()["internal_delivery_recorded"]
    expense_url = f"{root}/orders/{order_id}/cost-fixtures"
    expense = {"fixture_ref": "fixture:fulfillment-labor", "category": "FULFILLMENT", "amount_minor": 175}
    cost = client.post(expense_url, headers=owner, json=expense)
    assert cost.status_code == 201, cost.text
    assert client.post(expense_url, headers=owner, json=expense).json() == cost.json()
    assert client.post(expense_url, headers=owner, json={**expense, "amount_minor": 100}).status_code == 409
    assert cost.json()["fixture_contribution_minor"] == price - 175
    assert apply(refund, "evt_fixture_refund_one", price // 2).status_code == 200
    assert apply(refund, "evt_fixture_over_refund", price + 1).status_code == 409
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    assert apply(refund, "evt_fixture_refund_final", price).status_code == 200
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    final = client.get(f"{root}/orders/{order_id}").json()
    assert final["captured_minor"] == final["refunded_minor"] == price
    assert final["net_minor"] == 0
    assert final["verified_commercial_revenue"] is False
    assert summary()["rehearsed_net_minor"] == 0
    assert summary()["rehearsed_contribution_minor"] == -175
    assert summary()["actual_profit_minor"] is None
    assert summary()["verified_commercial_revenue"] is False
    from app.models.treasury_reconciliation import StatementAccount, StatementEntry, StatementImport

    for model in (StatementAccount, StatementEntry, StatementImport, FoundryFixtureSettlement):
        model.__table__.create(engine)
    statement_id = str(uuid4())
    today = date.today().isoformat()
    entries = [
        {"external_ref": "wrong-amount", "amount_minor": price + 1},
        {"external_ref": "capture-1", "amount_minor": price},
        {"external_ref": "refund-1", "amount_minor": -(price // 2)},
        {"external_ref": "refund-2", "amount_minor": -(price - price // 2)},
    ]
    statement = {"id": statement_id, "scope": scope, "source_id": "fixture:checkout-bank",
                 "account_ref": "fixture:payment-account", "purpose": "BUSINESS", "currency": "CAD",
                 "start": today, "end": today, "opening_minor": 0,
                 "closing_minor": sum(row["amount_minor"] for row in entries),
                 "outstanding_liabilities_minor": 0, "expense_budget_minor": 0,
                 "entries": [{**row, "posted_on": today, "category": "TRANSFER"} for row in entries],
                 "basis": "LOCAL_STATEMENT_FIXTURE"}
    imported = client.post("/api/governance/floor/treasury/statement-fixtures", headers=owner, json=statement)
    assert imported.status_code == 201, imported.text
    endpoint = f"{root}/orders/{order_id}/settlement-fixtures"
    link = {"statement_id": statement_id, "entry_ref": "wrong-amount", "payment_event_id": "evt_fixture_capture"}
    mismatch = client.post(endpoint, headers=owner, json=link)
    assert mismatch.json()["status"] == "DISCREPANCY" and mismatch.json()["difference_minor"] == 1
    link["entry_ref"] = "capture-1"
    matched = client.post(endpoint, headers=owner, json=link)
    assert matched.json()["status"] == "MATCHED_FIXTURE"
    assert matched.json()["actual_settlement_verified"] is False
    assert client.post(endpoint, headers=owner, json=link).json() == matched.json()
    assert client.post(endpoint, headers=owner, json={**link, "entry_ref": "wrong-amount"}).status_code == 409
    assert client.post(endpoint, headers=owner, json={
        **link, "entry_ref": "refund-1", "payment_event_id": "evt_fixture_refund_one",
    }).json()["status"] == "MATCHED_FIXTURE"

    assert client.post(endpoint, headers=owner, json={
        **link, "entry_ref": "refund-2", "payment_event_id": "evt_fixture_refund_final",
    }).json()["status"] == "MATCHED_FIXTURE"

    with Session(engine) as db:
        assert db.query(FoundryRehearsalPayment).count() == 3
    return final
