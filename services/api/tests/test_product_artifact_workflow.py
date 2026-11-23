import base64
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException
import pytest
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
    research_path = f"/api/prime/foundry/evidence/{evidence_id}/consumer-research"
    research = {
        "scope": scope, "observation_end": today.isoformat(), "source_basis": "SYNTHETIC", "aggregate_sample": 80,
        "observations": [{"signal": "UNDERSERVED_NEED", "count": 32}, {"signal": "CHECKOUT_FRICTION", "count": 12},
                         {"signal": "PRICE_OBJECTION", "count": 20}, {"signal": "VOLUNTARY_REFERRAL", "count": 10}],
        "offer_experiment": [{"cad_price_minor": 2500, "exposed": 40, "chose_offer": 18},
                             {"cad_price_minor": 3000, "exposed": 40, "chose_offer": 16}],
        "transparent_offer_and_terms": True, "voluntary_participation": True, "no_deceptive_claims_or_urgency": True,
        "no_sensitive_profiling_or_vulnerability_targeting": True,
        "no_fake_endorsements_or_manipulative_interfaces": True,
    }
    assert client.post(research_path, json=research).status_code == 401
    assert client.post(research_path, headers=owner,
                       json={**research, "no_deceptive_claims_or_urgency": False}).status_code == 422
    assert client.post(research_path, headers=owner,
                       json={**research, "observations": [{"signal": "PRICE_OBJECTION", "count": 2}]}).status_code == 422
    recorded = client.post(research_path, headers=owner, json=research)
    assert recorded.status_code == 201, recorded.text
    aggregate = recorded.json()
    assert client.post(research_path, headers=owner, json=research).json() == aggregate
    assert client.post(research_path, headers=owner, json={**research, "aggregate_sample": 81}).status_code == 409
    assert aggregate["price_signal"] == "NO_CLEAR_SEPARATION" and aggregate["causality_verified"] is False
    assert {"SIMPLIFY_CHECKOUT", "TEST_TRANSPARENT_PRICING"} <= set(aggregate["research_actions"])
    with Session(engine) as db:
        specialist_report_id = run_assignment(db, "ODIN", now=tick)["report_event_id"]
    source_report = client.get(f"/api/prime/pantheon/reports/{specialist_report_id}").json()
    assert source_report["trigger"] == "SOURCE_DISCOVERY"
    candidate = client.get(f"/api/prime/foundry/reports/{specialist_report_id}/candidate/{evidence_id}")
    assert candidate.status_code == 200, candidate.text
    grounded = candidate.json()["proposal"]
    proposal = {**proposal, **grounded, "persist_decision": True,
                "specialist_inputs": {**proposal["specialist_inputs"], **grounded["specialist_inputs"]}}
    assert proposal["specialist_inputs"]["discovery_demand"]["sample_demand_bp"] == 7500
    assert proposal["specialist_inputs"]["consumer_research"] == aggregate
    for model in (MarketingCampaign, FoundryRehearsalOrder, FoundryRehearsalPayment, FoundryCampaignVisit):
        model.__table__.create(engine)
    with Session(engine) as db:
        db.add(MarketingCampaign(id=1, name="Private rehearsal", strategy_payload="{}"))
        db.add(MarketingCampaign(id=2, name="Comparable rehearsal control", strategy_payload="{}"))
        db.commit()
    acquisition = "/api/prime/foundry/rehearsal/campaigns/1"
    plan = {"scope": scope, "demand_evidence_id": evidence_id, "channel": "DIRECT_OPT_IN",
            "experiment_budget_minor": 100, "stop_after_visits": 2}
    assert client.post(f"{acquisition}/acquisition-plan", json=plan).status_code == 401
    assert client.post(f"{acquisition}/acquisition-plan", headers=owner,
                       json={**plan, "experiment_budget_minor": 101}).status_code == 409
    planned = client.post(f"{acquisition}/acquisition-plan", headers=owner, json=plan)
    assert planned.status_code == 201, planned.text
    assert planned.json()["target_buyer_segment"] == "Practice workshop operators"
    assert planned.json()["spend_authorized"] is False
    assert planned.json()["consumer_research"]["sha256"] == aggregate["sha256"]
    control = client.post("/api/prime/foundry/rehearsal/campaigns/2/acquisition-plan", headers=owner, json=plan)
    assert control.status_code == 201, control.text

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
    assert any(item["category"] == "consumer_evidence_limits" for item in specialist_result["findings"])
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
    assert decision_turn["evidence"]["reviewed_specialist_reports"] == advice["independent_loki"]["reviewed_specialist_reports"]
    behavioural_review = decision_turn["evidence"]["reviewed_consumer_research"]
    assert behavioural_review == advice["independent_loki"]["reviewed_consumer_research"]
    assert behavioural_review["sha256"] == aggregate["sha256"] and not behavioural_review["settled_conversion_verified"]
    from app.services.foundry_discovery import require_current_candidate

    with Session(engine) as db:
        forged = {**proposal, "specialist_inputs": {**proposal["specialist_inputs"],
                  "consumer_research": {**aggregate, "causality_verified": True}}}
        with pytest.raises(HTTPException, match="source-bound candidate"):
            require_current_candidate(db, forged, scope, today)
    assignment_id = UUID(source_report["assignment_id"])
    with Session(engine) as db:
        db.get(SpecialistAssignment, assignment_id).scope = {**scope, "jurisdiction": "CA-ON"}
        db.commit()
    rejected = evaluate()
    assert rejected.status_code == 409 and "outside decision scope" in rejected.json()["detail"]
    stale_context = client.post(turns, json={"turn_id": str(uuid4()), "message": "Check specialist authority",
                                             "prime_decision_id": listing["prime_verdict_id"]})
    assert stale_context.status_code == 409 and "outside decision scope" in stale_context.json()["detail"]
    with Session(engine) as db:
        db.get(SpecialistAssignment, assignment_id).scope = scope
        db.commit()
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
    from app.models.stripe_finance import StripeBalanceEvidence, StripeFinancialEvent, StripeOrderBinding

    for model in (StripeFinancialEvent, StripeBalanceEvidence, StripeOrderBinding):
        model.__table__.create(engine)
    monkeypatch.setenv("VALHALLA_STRIPE_EVENT_MODE", "test")
    monkeypatch.setenv("VALHALLA_STRIPE_ACCOUNT_ID", "acct_FoundryTest")
    monkeypatch.setattr("app.routers.stripe_financial.is_live", lambda: False)
    order_bind = {"order_id": str(uuid4()), "action_id": action_id, "scope": scope,
                  "payment_intent_id": "pi_ProductApprovalTest"}
    binding_path = "/api/governance/floor/stripe-orders"
    wrong_scope = {**scope, "business_id": "another-business"}
    assert client.post(binding_path, headers=owner, json={**order_bind, "scope": wrong_scope}).status_code == 409
    bind = client.post(binding_path, headers=owner, json=order_bind)
    assert bind.status_code == 201, bind.text
    assert bind.json()["amount_minor"] == listing["price_cents_cad"]
    assert bind.json()["product_asset_id"] == str(asset_id)
    assert bind.json()["payment_created"] is False
    assert client.post(binding_path, headers=owner, json={**order_bind,
                       "order_id": str(uuid4()), "payment_intent_id": "pi_fixture_product"}).status_code == 422

    acquisition_review = client.post(f"{acquisition}/settled-review", json=scope)
    assert acquisition_review.status_code == 200, acquisition_review.text
    review = acquisition_review.json()
    assert review["settled_conversion_bp"] == 5000 and review["retained_net_order_conversion_bp"] == 0
    assert review["contribution_minor"] == -175 and review["recommendation"] == "RECOMMEND_PAUSE"
    assert review["consent_receipt_count"] == 2 and len(review["consent_evidence_sha256"]) == 64
    assert review["research_relationship"]["consumer_research_sha256"] == aggregate["sha256"]
    assert review["research_relationship"]["campaign_causality_verified"] is False
    comparison_path = "/api/prime/foundry/rehearsal/campaign-comparisons"
    comparison = {"scope": scope, "campaign_ids": [2, 1], "minimum_visits": 20}
    compared = client.post(comparison_path, json=comparison)
    assert compared.status_code == 200, compared.text
    assert [arm["decision"] for arm in compared.json()["arms"]] == ["CONTINUE_TESTING", "CONTINUE_TESTING"]
    assert compared.json()["consumer_research_sha256"] == aggregate["sha256"]
    assert compared.json()["external_action_authorized"] is False
    comparison_artifact = client.post(comparison_path + "/review-artifact", headers=owner, json=comparison)
    assert comparison_artifact.status_code == 200 and comparison_artifact.json()["raw_input"] == compared.json()
    comparison_review = client.post("/loki/reviews", json=comparison_artifact.json())
    assert comparison_review.status_code == 201, comparison_review.text
    comparison_review_id = comparison_review.json()["id"]
    review_path = comparison_path + "/reviewed"
    review_request = {**comparison, "independent_review_id": comparison_review_id}
    assert client.post(review_path, headers=owner, json=review_request).status_code == 409
    reviewer_queue = client.get("/loki/worker/reviews", headers=worker,
                                params={"artifact_type": "acquisition_comparison"}).json()
    queued_comparison = next(item for item in reviewer_queue if item["review_id"] == comparison_review_id)
    analysis = challenge(queued_comparison).model_dump(mode="json")
    assert client.post(f"/loki/worker/reviews/{comparison_review_id}/result", headers=worker,
                       json=analysis).status_code == 201
    assert client.post(review_path, headers=owner, json=review_request).status_code == 409
    objections = client.get(f"/loki/reviews/{comparison_review_id}/findings").json()
    reconsidered = client.post(f"/loki/reviews/{comparison_review_id}/reconsider", headers=owner, json={
        "artifact_sha256": analysis["artifact_sha256"], "disposition": "accept_risk",
        "material_finding_ids": [item["id"] for item in objections],
        "reason": "Confirmed this is an isolated comparison with insufficient data to scale.",
    })
    assert reconsidered.status_code == 200, reconsidered.text
    reviewed = client.post(review_path, headers=owner, json=review_request)
    assert reviewed.status_code == 201, reviewed.text
    reviewed_campaign = reviewed.json()
    assert reviewed_campaign["economic_mandate_id"] == capital_mandate["id"]
    assert reviewed_campaign["capital_reserved_minor"] == reviewed_campaign["simulated_followup_cap_minor"] == 0
    assert client.post(review_path, headers=owner, json=review_request).json() == reviewed_campaign
    assert client.post(review_path, headers=owner, json={**review_request, "minimum_visits": 21}).status_code == 409
    assert review["plan_sha256"] == planned.json()["sha256"] and not review["verified_commercial_revenue"]
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

    proof_route = f"/api/prime/foundry/rehearsal/orders/{closed_order['order_id']}/closed-checkout-proof"
    proof_response = client.get(proof_route)
    assert proof_response.status_code == 200, proof_response.text
    proof = proof_response.json()
    assert proof["scope"] == scope and proof["internal_delivery_recorded"]
    assert proof["verified_commercial_revenue"] is False and len(proof["settlements"]) == 3
    adverse = {**performance, "id": str(uuid4()), "start": today.isoformat(), "end": today.isoformat(),
               "operating_receipts": closed_order["net_minor"], "operating_costs": closed_order["fixture_cost_minor"],
               "receipt_ref": f"checkout-fixture:{closed_order['order_id']}",
               "checkout_order_id": closed_order["order_id"], "checkout_sha256": proof["sha256"]}
    economic("performance", {**adverse, "operating_receipts": 1}, 409)
    economic("performance", {**adverse, "checkout_sha256": "0" * 64}, 409)
    booked_checkout = economic("performance", adverse)
    assert economic("performance", adverse) == booked_checkout
    economic("performance", {**adverse, "id": str(uuid4())}, 409)
    economic("mandates", {**capital_mandate, "id": str(uuid4()), "previous_id": capital_mandate["id"]})
    after = economic("assessment", scope, 200)
    assert after["period_net_minor"] == -175 and after["cumulative_loss_minor"] == 175
    assert after["suggested_action"] == "EXIT"

    owner_operating_route = "/api/weweb/owner-operating-scope"
    from app.routers.auth_weweb import require_owner_session

    assert client.post(owner_operating_route, json=scope).status_code == 401
    with monkeypatch.context() as owner_fixture:
        owner_fixture.setitem(client.app.dependency_overrides, require_owner_session, lambda: 1)
        operating = client.post(owner_operating_route, json=scope)
        assert operating.status_code == 200 and operating.headers["cache-control"] == "no-store"
        view = operating.json()
        assert view["execution_authorized"] is False and view["actual_accessible_funds_minor"] is None
        assert view["recurring_paid_periods"] is None
        assert view["capital_fixture"]["period_net_minor"] == -175
        assert view["statement_fixtures"]["BUSINESS"]["accounts"][0]["status"] == "MATCHED_FIXTURE"
        assert view["statement_fixtures"]["HOUSEHOLD"]["accounts"] == []
        assert view["statement_fixtures"]["OPERATING_RESERVE"]["accounts"] == []
        assert client.post(owner_operating_route, json={**scope, "jurisdiction": "CA-ON"}).status_code == 409
        recurring = {"basis": "STRIPE_TEST_PAID_PERIODS", "status": "OBSERVED",
                     "verified_current_periods": 2, "verified_adjacent_renewals": 1,
                     "scheduled_cancellations": 0, "held_agreements": 0,
                     "available_cash_minor": None, "recognized_revenue_minor": None, "external_authority": False}

        def recurring_fixture(db, selected_scope, *, live):
            assert selected_scope == scope
            return recurring

        owner_fixture.setattr("app.services.stripe_recurring.scoped_subscription_outcomes", recurring_fixture)
        scoped = client.post(owner_operating_route, json=scope)
        assert scoped.status_code == 200 and scoped.headers["cache-control"] == "no-store"
        assert scoped.json()["recurring_paid_periods"] == recurring
        assert scoped.json()["actual_accessible_funds_minor"] is None

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
    assert learned_response["observations"]["acquisition_rehearsal"][0]["sha256"] == review["sha256"]
    history = learned_response["observations"]["reviewed_acquisition_history"][0]
    assert history["status"] == "HISTORICAL_REVIEW_ONLY" and history["sha256"] == reviewed_campaign["sha256"]
    assert learned_response["observations"]["checkout_learning"][0]["fixture_contribution_minor"] == -175
    assert learned_response["observations"]["economic_reassessment"]["cumulative_loss_minor"] == 175
    next_tick = datetime.fromisoformat(next_cadence).replace(tzinfo=None) + timedelta(seconds=1)
    pantheon_root = "/api/prime/pantheon"
    forseti = client.post(f"{pantheon_root}/assignments", headers=owner, json={
        **scope, "assignment_id": str(uuid4()), "role": "FORSETI",
        "cadence_seconds": 120, "duration_seconds": 1800,
    })
    assert forseti.status_code == 201, forseti.text
    review_at = datetime.fromisoformat(forseti.json()["next_due_at"]).replace(tzinfo=None) + timedelta(seconds=1)
    with Session(engine) as db:
        checked = run_assignment(db, "FORSETI", now=review_at)
    check_path = f"{pantheon_root}/reports/{checked['report_event_id']}"
    observations = client.get(check_path).json()["observations"]
    assert observations["checkout_learning"][0]["status"] == "MATCHED_FIXTURE"
    assert observations["factory_evidence_reconciliation"]["contradictions"] == []

    with Session(engine) as db:
        settlement = db.get(FoundryFixtureSettlement, "evt_fixture_capture")
        settlement.amount_minor += 1
        db.commit()
        assert run_due_schedule(db, now=next_tick)["status"] == "evaluated"
        checked = run_assignment(db, "FORSETI", now=review_at + timedelta(seconds=120))
    conflicted = client.get(f"{pantheon_root}/reports/{checked['report_event_id']}").json()
    [checkout_evidence] = conflicted["observations"]["checkout_learning"]
    assert checkout_evidence["status"] == "EVIDENCE_CONFLICT"
    assert checkout_evidence["verified_commercial_revenue"] is False
    from app.loki.evidence import artifact_digest

    challenged_report = challenge({
        "artifact_type": "pantheon_report", "reference": conflicted["report_event_id"],
        "raw_input": conflicted,
        "artifact_sha256": artifact_digest("pantheon_report", conflicted["report_event_id"], conflicted),
    })
    assert any(f.category == "checkout_evidence_conflict" and f.severity == "critical"
               for f in challenged_report.findings)
    contradicted = client.get(f"{schedule_root}/{schedule_id}").json()["latest_report"]
    assert "CHECKOUT_EVIDENCE_CONFLICT" in contradicted["operating_reassessment"]["blockers"]
    assert "CHECKOUT_PERFORMANCE_EVIDENCE_CONFLICT" in contradicted["operating_reassessment"]["blockers"]
    assert contradicted["operating_reassessment"]["economic_reassessment"]["cumulative_loss_minor"] == 175
    assert contradicted["operating_reassessment"]["economic_reassessment"]["new_exposure_available_minor"] == 0
    assert contradicted["recommendation"]["heimdall_decision"] == "HOLD"
    assert client.get(f"{schedule_root}/{schedule_id}/reports/{report['report_event_id']}").json() == report
    with Session(engine) as db:
        assert db.query(MediaContent).count() == 1
        learned = db.query(LegacyOrchestrationEvent).filter_by(event_type="MIMIR_INTERNAL_ARTIFACT_VERIFIED").one()
        verified = json.loads(learned.payload_json)
        assert verified["product_asset"]["sha256"] == checksum
        assert verified["prime_decision"]["proposal_sha256"] == artifact["artifact_sha256"]
    performance_claim = {"basis": "ECONOMIC_PERFORMANCE_FIXTURE", "record_id": booked_checkout["id"],
                         "sha256": booked_checkout["sha256"], "period_net_minor": -175}
    from app.services.prime_business_execution import verify_mimir_claims

    assert client.get(proof_route).status_code == 409
    with Session(engine) as db:
        with pytest.raises(HTTPException, match="closed checkout"):
            verify_mimir_claims(db, scope, [performance_claim])
        db.get(FoundryFixtureSettlement, "evt_fixture_capture").amount_minor -= 1
        db.commit()
    # Exercise the current proof through independent review, persisted advice and the Factory boundary.
    history = report["verified_internal_outcomes"][0]
    claim = {key: history[key] for key in ("outcome_event_id", "artifact_sha256", "sales_verified")}
    reviewed_inputs = {key: value for key, value in proposal["specialist_inputs"].items()
                       if key not in {"pantheon_report_ids", "foundry_evidence", "foundry_economics",
                                      "discovery_demand", "consumer_research"}}
    forecast_claim = {"basis": "NORNS_FACTORY_DEADLINE", "forecast_id": forecast_id,
                      "sha256": resolved.json()["resolution_sha256"], "observed_outcome": 1}
    reviewed_inputs["mimir_outcome_claims"] = [claim, forecast_claim, performance_claim]
    followup = {**proposal, "opportunity_id": "product-history-follow-up", "source": "internal",
                "specialist_inputs": reviewed_inputs}
    current_artifact = client.post(f"{PHASE3}/review-artifact", json=followup).json()
    queued_review = client.post("/loki/reviews", json={**current_artifact, "input_source": "history-rehearsal"})
    assert queued_review.status_code == 201, queued_review.text
    claim_review = queued_review.json()["id"]
    observed = client.post(f"/loki/worker/reviews/{claim_review}/result", headers=worker, json={
        "artifact_sha256": current_artifact["artifact_sha256"], "analysis_ref": "fixture:historical-proof-review",
        "summary": "Verified scoped internal use of the cited artifact.", "findings": [],
    })
    assert observed.status_code == 201, observed.text
    followup_result = client.post(f"{PHASE3}/evaluate", json={
        "opportunities": [{**followup, "independent_loki_review_id": claim_review}], "shadow_mode": False,
    })
    assert followup_result.status_code == 200, followup_result.text
    next_advice = followup_result.json()["evaluations"][0]
    assert next_advice["independent_loki"]["reviewed_mimir_outcomes"] == [
        {**claim, "evidence_scope": "INTERNAL_ARTIFACT_ONLY"},
        {**forecast_claim, "evidence_scope": "INTERNAL_FACTORY_DEADLINE_ONLY",
         "evidence_ref": resolved.json()["evidence_ref"], "commercial_result": False},
        {**performance_claim, "evidence_scope": "ECONOMIC_PERFORMANCE_FIXTURE_ONLY",
         "checkout_order_id": closed_order["order_id"], "checkout_sha256": proof["sha256"],
         "verified_real_world_outcome": False},
    ]
    followup_listing = {**listing, "request_key": "history-bound-listing",
                        "prime_verdict_id": next_advice["persistence"]["god_verdict_id"]}
    fresh_context = owner_turn("Show the verified history behind this proposal", prime_decision_id=followup_listing["prime_verdict_id"])
    assert fresh_context["evidence"]["reviewed_mimir_outcomes"] == next_advice["independent_loki"]["reviewed_mimir_outcomes"]
    assert fresh_context["execution_authorized"] is False
    decision_route = f"/api/weweb/owner-prime-decisions/{followup_listing['prime_verdict_id']}"
    with monkeypatch.context() as route_fixture:
        route_fixture.setitem(client.app.dependency_overrides, require_owner_session, lambda: 1)
        direct = client.get(decision_route)
    assert direct.status_code == 200, direct.text
    assert direct.headers["cache-control"] == "no-store"
    assert direct.json()["independent_loki"]["review_id"] == claim_review
    assert direct.json()["reviewed_mimir_outcomes"] == next_advice["independent_loki"]["reviewed_mimir_outcomes"]
    still_held = client.post(f"{FACTORY}/listing-drafts", headers=admin, json=followup_listing)
    assert still_held.status_code == 409 and "containment" in still_held.json()["detail"]
    with Session(engine) as db:
        historical = db.get(NornsForecast, UUID(forecast_id))
        historical.observed_outcome = 0
        db.commit()
    altered_forecast = client.post(f"{FACTORY}/listing-drafts", headers=admin, json=followup_listing)
    assert altered_forecast.status_code == 409 and "forecast claim" in altered_forecast.json()["detail"]
    with Session(engine) as db:
        historical = db.get(NornsForecast, UUID(forecast_id))
        historical.observed_outcome = 1
        db.add(NornsHoldout(forecast_id=historical.id, enrolled_at=historical.issued_at))
        db.commit()
    holdout_forecast = client.post(f"{FACTORY}/listing-drafts", headers=admin, json=followup_listing)
    assert holdout_forecast.status_code == 409 and "ordinary-cohort" in holdout_forecast.json()["detail"]
    from app.models.completion_registry import LegacyGovernancePolicy, LegacyInstancePolicyState
    for model in (LegacyGovernancePolicy, LegacyInstancePolicyState):
        model.__table__.create(engine, checkfirst=True)
    with Session(engine) as db:
        legacy = db.query(LegacyInstanceRegistryItem).filter_by(legacy_instance_id=scope["legacy_instance_id"]).one()
        policy = {"policy_id": "workflow-fixture", "policy_version": "v1"}
        context = json.loads(legacy.local_knowledge_context_json)
        legacy.local_knowledge_context_json = json.dumps({**context, "governance": policy})
        db.add(LegacyGovernancePolicy(**policy, policy_scope="GLOBAL", autonomy_policy_json="{}",
                                     ethics_evidence_policy_json="{}", kill_shield_policy_json="{}",
                                     engine_activation_policy_json="{}", jurisdiction_restrictions_json="{}",
                                     approval_requirements_json="{}", audit_requirements_json="{}"))
        db.add(LegacyInstancePolicyState(legacy_instance_id=scope["legacy_instance_id"], **policy))
        db.commit()
    path = "/api/prime/legacy-playbooks/workflow-versions"
    reusable = client.post(path + "/record", headers=owner, json={
        "scope": scope, "name": "exact-product-draft", "version": 1, "outcome_ids": [claim["outcome_event_id"]],
        "input_contract": ["Approved product draft"], "acceptance_checks": ["Product asset digest verified"],
        "rollback_procedure": "Discard the draft and retain the last reviewed version.", "data_class": "SYNTHETIC",
    })
    assert reusable.status_code == 201, reusable.text
    evidence = reusable.json()
    assert evidence["verified_internal_outcomes"][0]["artifact_sha256"] == claim["artifact_sha256"]
    measurement = evidence["verified_internal_outcomes"][0]["execution_observation"]
    assert measurement["kind"] == "INTERNAL_DETERMINISTIC_DRAFT"
    assert measurement["elapsed_ms"] >= 0 and measurement["provider_calls"] == 0
    assessment = {
        "source": scope, "target": scope, "name": "exact-product-draft", "version": 1,
        "expected_sha256": evidence["sha256"], "data_class": "SYNTHETIC",
    }
    advice = client.post(path + "/assess", headers=admin, json=assessment)
    assert advice.status_code == 200 and advice.json()["status"] == "REUSE_REVIEW_REQUIRED"
    assert advice.json()["execution_authorized"] is False
    assert advice.json()["historical_draft_baseline"] == {
        "sample_count": 1, "median_elapsed_ms": measurement["elapsed_ms"],
        "provider_cost_minor_cad": 0, "includes_failed_attempts": False,
    }

    with Session(engine) as db:
        db.delete(db.get(NornsHoldout, UUID(forecast_id)))
        event = db.query(LegacyOrchestrationEvent).filter_by(event_id=claim["outcome_event_id"]).one()
        event.payload_json = "{}"
        db.commit()
    stale_baseline = client.post(path + "/assess", headers=admin, json=assessment).json()
    assert stale_baseline["status"] == "REUSE_REVIEW_REQUIRED"
    assert stale_baseline["historical_draft_baseline"]["sample_count"] == 0
    refused = client.post(f"{FACTORY}/listing-drafts", headers=admin, json=followup_listing)
    assert refused.status_code == 409
    assert refused.json()["detail"]["outcome_event_id"] == claim["outcome_event_id"]
    stale_context = client.post(turns, json={
        "turn_id": str(uuid4()), "message": "Check the reviewed evidence again",
        "prime_decision_id": followup_listing["prime_verdict_id"],
    })
    assert stale_context.status_code == 409
    assert stale_context.json()["detail"]["outcome_event_id"] == claim["outcome_event_id"]
    assert client.delete(f"{ASSETS}/{asset_id}", headers=admin).status_code == 401
    assert client.delete(f"{ASSETS}/{asset_id}", headers=owner).json()["revoked"]
    assert client.get(download_url, headers=owner).status_code == 409


def rehearse_checkout(client, engine, monkeypatch, owner, action_id, price, scope):
    import hmac
    import time

    secret = "fixture-test-secret"
    monkeypatch.setenv("VALHALLA_FOUNDRY_FIXTURE_SECRET", secret)
    root = "/api/prime/foundry/rehearsal"
    visit_ids = [str(uuid4()), str(uuid4())]
    assert client.post(f"{root}/campaign-visits", json={**scope, "campaign_id": 1, "visit_id": visit_ids[0]}).status_code == 401
    assert client.post(f"{root}/campaign-visits", headers=owner,
                       json={**scope, "campaign_id": 1, "visit_id": visit_ids[0]}).status_code == 409
    for visit_id in visit_ids:
        details = {**scope, "campaign_id": 1, "visit_id": visit_id, "consent_fixture_id": str(uuid4())}
        visit = client.post(f"{root}/campaign-visits", headers=owner, json=details)
        assert visit.status_code == 201, visit.text
        assert client.post(f"{root}/campaign-visits", headers=owner, json=details).json() == visit.json()
        assert client.post(f"{root}/campaign-visits", headers=owner,
                           json={**details, "consent_fixture_id": str(uuid4())}).status_code == 409
        assert client.post(f"{root}/campaign-visits", headers=owner,
                           json={**details, "visit_id": str(uuid4())}).status_code == 409
    capped = client.post(f"{root}/campaign-visits", headers=owner, json={
        **scope, "campaign_id": 1, "visit_id": str(uuid4()), "consent_fixture_id": str(uuid4()),
    })
    assert capped.status_code == 409 and "visit limit" in capped.json()["detail"]
    rehearse_channel_intent(client, engine, monkeypatch, owner, scope, visit_ids)
    suppression = {"consent_fixture_id": details["consent_fixture_id"], **scope}
    endpoint = f"{root}/consent-suppressions"
    assert client.post(endpoint, json=suppression).status_code == 401
    receipt = client.post(endpoint, headers=owner, json=suppression)
    assert receipt.status_code == 201 and receipt.json()["status"] == "SUPPRESSED_IN_FIXTURE"
    assert client.post(endpoint, headers=owner, json=suppression).json() == receipt.json()
    assert client.post(f"{root}/campaign-visits", headers=owner,
                       json={**details, "campaign_id": 2, "visit_id": str(uuid4())}).status_code == 409
    assert client.post(f"{root}/campaign-visits", headers=owner, json=details).status_code == 201
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
    withdrawn = client.post(f"{root}/orders", headers=owner, json={
        **payload, "visit_id": visit_ids[1],
    })
    assert withdrawn.status_code == 409 and "opt-in was withdrawn" in withdrawn.json()["detail"]
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
    assert paid.json()["checkout_state"] == "PAID_AWAITING_DELIVERY"
    assert apply(capture, "evt_fixture_capture", price).json() == paid.json()
    assert summary()["rehearsed_conversions"] == 1
    assert summary()["rehearsed_net_minor"] == price
    assert apply(capture, "evt_fixture_capture", price + 5).status_code == 409
    exception = f"{root}/orders/{order_id}/fulfillment-exception"
    hold = {"event_id": str(uuid4()), "action": "HOLD", "reason": "Review an internal fulfillment exception."}
    assert client.post(exception, json=hold).status_code == 401
    held = client.post(exception, headers=owner, json=hold)
    assert held.status_code == 200, held.text
    assert held.json()["fulfillment_exception"]["status"] == "HELD"
    assert held.json()["owner_followup_required"] is True
    from app.loki.analyst import challenge
    from app.loki.evidence import artifact_digest
    from types import SimpleNamespace

    from app.routers.foundry_checkout import scoped_checkout_learning
    from app.routers.prime_specialist_schedules import attach_operating_reassessment
    from app.services.checkout_operating_signals import checkout_operating_blockers
    from app.services.prime_business_execution import verified_internal_outcomes

    with Session(engine) as db:
        outcomes = verified_internal_outcomes(db, **scope)
        [held_observation] = scoped_checkout_learning(db, scope, outcomes)
        reassessment = {"recommendation": {"heimdall_decision": "EVALUATE"}}
        scheduled = SimpleNamespace(opportunity=SimpleNamespace(specialist_inputs={}, source="internal"))
        attach_operating_reassessment(db, scheduled, scope, _utc_now().date(), outcomes, reassessment)
    assert "CHECKOUT_FULFILLMENT_HELD" in reassessment["operating_reassessment"]["blockers"]
    assert reassessment["recommendation"]["heimdall_decision"] == "HOLD"
    assert held_observation["status"] == "UNRECONCILED_FIXTURE"
    assert held_observation["unmatched_fixture_payment_ids"] == ["evt_fixture_capture"]
    assert "CHECKOUT_FULFILLMENT_HELD" in checkout_operating_blockers([held_observation])
    review_ref = "checkout-hold-fixture"
    report = {"status": "observed", "external_authority": False,
              "observations": {"checkout_learning": [held_observation]}}
    held_review = challenge({"artifact_type": "pantheon_report", "reference": review_ref, "raw_input": report,
                             "artifact_sha256": artifact_digest("pantheon_report", review_ref, report)})
    assert any(item.category == "checkout_review_pending" and item.severity == "critical"
               for item in held_review.findings)
    assert client.post(f"{root}/orders/{order_id}/delivery", headers=owner).status_code == 409
    release = {"event_id": str(uuid4()), "action": "RELEASE_FOR_RETRY", "reason": "Internal artifact reviewed and ready."}
    assert client.post(exception, headers=owner, json=release).status_code == 409
    release["previous_event_id"] = hold["event_id"]
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    assert client.post(exception, headers=owner, json=release).status_code == 503
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    released = client.post(exception, headers=owner, json=release)
    assert released.status_code == 200, released.text
    assert released.json()["fulfillment_exception"]["status"] == "RETRY_REVIEWED"
    assert client.post(exception, headers=owner, json=release).json() == released.json()
    delivered = client.post(f"{root}/orders/{order_id}/delivery", headers=owner)
    assert delivered.status_code == 200, delivered.text
    assert delivered.json()["internal_delivery_recorded"]
    assert delivered.json()["checkout_state"] == "DELIVERED_INTERNAL"
    expense_url = f"{root}/orders/{order_id}/cost-fixtures"
    expense = {"fixture_ref": "fixture:fulfillment-labor", "category": "FULFILLMENT", "amount_minor": 175}
    cost = client.post(expense_url, headers=owner, json=expense)
    assert cost.status_code == 201, cost.text
    assert client.post(expense_url, headers=owner, json=expense).json() == cost.json()
    assert client.post(expense_url, headers=owner, json={**expense, "amount_minor": 100}).status_code == 409
    assert cost.json()["fixture_contribution_minor"] == price - 175
    partial = apply(refund, "evt_fixture_refund_one", price // 2)
    assert partial.status_code == 200
    assert partial.json()["checkout_state"] == "PARTIALLY_REFUNDED"
    assert partial.json()["owner_followup_required"] is True
    partial_observation = {**partial.json(), "status": "UNRECONCILED_FIXTURE"}
    assert "CHECKOUT_REFUND_REVIEW_REQUIRED" in checkout_operating_blockers([partial_observation])
    assert apply(refund, "evt_fixture_refund_one", price // 2).json() == partial.json()
    assert apply(refund, "evt_fixture_duplicate_total", price // 2).status_code == 409
    assert apply(refund, "evt_fixture_over_refund", price + 1).status_code == 409
    support = f"{root}/orders/{order_id}/support-resolution"
    resolution = {"expected_refunded_minor": price // 2, "resolution": "Reviewed the partial refund fixture."}
    assert client.post(support, json=resolution).status_code == 401
    closed = client.post(support, headers=owner, json=resolution)
    assert closed.status_code == 200, closed.text
    assert closed.json()["owner_followup_required"] is False
    assert closed.json()["support_resolution"]["external_customer_action_verified"] is False
    assert client.post(support, headers=owner, json=resolution).json() == closed.json()
    assert client.post(support, headers=owner, json={**resolution, "resolution": "Different review note."}).status_code == 409
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    assert apply(refund, "evt_fixture_refund_final", price).status_code == 200
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    final = client.get(f"{root}/orders/{order_id}").json()
    assert final["captured_minor"] == final["refunded_minor"] == price
    assert final["net_minor"] == 0
    assert final["checkout_state"] == "REFUNDED" and final["owner_followup_required"] is True
    assert final["verified_commercial_revenue"] is False
    assert final["support_resolution"] is None
    assert client.post(support, headers=owner, json=resolution).status_code == 409
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    final_closed = client.post(support, headers=owner, json={**resolution, "expected_refunded_minor": price})
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    assert final_closed.status_code == 200, final_closed.text
    assert final_closed.json()["owner_followup_required"] is False
    assert final_closed.json()["support_resolution"]["event_id"] != closed.json()["support_resolution"]["event_id"]

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
    assert client.get(f"{root}/orders/{order_id}/closed-checkout-proof").status_code == 409
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


def rehearse_channel_intent(client, engine, monkeypatch, owner, scope, visit_ids):
    import hmac

    from app.loki.evidence import artifact_digest
    from app.models.media_engine import MediaChannel, MediaPublishLog

    for model in (MediaChannel, MediaPublishLog):
        model.__table__.create(engine)
    key = "isolated-channel-fixture-only"
    monkeypatch.setenv("VALHALLA_ACQUISITION_CHANNEL_FIXTURE_KEY", key)
    with Session(engine) as db:
        channel = MediaChannel(name="Internal synthetic opt-in", slug="fixture-direct")
        db.add(channel)
        db.flush()
        entry = MediaPublishLog(content_id=db.query(MediaContent).one().id, channel_id=channel.id, status="planned")
        db.add(entry)
        db.commit()
        media_id = entry.id
    root = "/api/prime/foundry/rehearsal"
    intent = {"intent_id": str(uuid4()), "scope": scope, "campaign_id": 1, "media_publish_id": media_id,
              "scheduled_at": datetime.now(timezone.utc).isoformat(), "reviewed_transparent_copy": True,
              "visit_id": visit_ids[0]}
    assert client.post(f"{root}/channel-intents", json=intent).status_code == 401
    staged = client.post(f"{root}/channel-intents", headers=owner, json=intent)
    assert staged.status_code == 201, staged.text
    assert client.post(f"{root}/channel-intents", headers=owner, json=intent).json() == staged.json()
    receipt = {"intent_id": intent["intent_id"], "scope": scope, "provider_fixture_event_id": str(uuid4()),
               "expected_intent_sha256": staged.json()["sha256"], "outcome": "ACCEPTED_IN_FIXTURE"}

    def post_receipt(body, valid=True):
        digest = artifact_digest("acquisition_channel_provider_fixture", body["provider_fixture_event_id"], body)
        signature = hmac.new(key.encode(), digest.encode(), hashlib.sha256).hexdigest() if valid else "invalid"
        return client.post(f"{root}/channel-fixture-receipts", headers={"X-Acquisition-Fixture-Signature": signature}, json=body)

    assert post_receipt(receipt, valid=False).status_code == 401
    assert post_receipt({**receipt, "expected_intent_sha256": "0" * 64}).status_code == 409
    with Session(engine) as db:
        row = db.get(MediaPublishLog, media_id)
        row.status = "cancelled"
        db.commit()
    assert post_receipt(receipt).status_code == 409
    with Session(engine) as db:
        row = db.get(MediaPublishLog, media_id)
        row.status = "planned"
        db.commit()
    accepted = post_receipt(receipt)
    assert accepted.status_code == 201, accepted.text
    assert accepted.json()["status"] == "ACCEPTED_IN_FIXTURE"
    assert accepted.json()["publication_verified"] is False
    assert post_receipt(receipt).json() == accepted.json()
    assert post_receipt({**receipt, "outcome": "REJECTED_IN_FIXTURE"}).status_code == 409
    with Session(engine) as db:
        row = db.get(MediaPublishLog, media_id)
        assert row.status == "planned" and row.external_ref is None
