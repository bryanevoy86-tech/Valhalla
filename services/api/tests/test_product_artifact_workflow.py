import base64
import hashlib
import json
from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.god.models import GodReviewCase, GodReviewEvent
from app.loki.models import LokiFinding, LokiIndependentReceipt, LokiReconsideration, LokiReview
from app.models.god_verdicts import GodVerdict
from app.models.governance_decision import GovernanceDecision
from app.models.completion_registry import (
    KnowledgeRegistryItem, LearningFeedbackRecord, LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent,
)
from app.models.media_engine import MediaContent
from app.models.owner_conversation import OwnerConversation, OwnerTurn
from app.models.product_artifact import ProductArtifact
from app.models.prime_specialist_schedule import PrimeSpecialistSchedule
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
    for model in (KnowledgeRegistryItem, LearningFeedbackRecord, PrimeSpecialistSchedule, OwnerConversation, OwnerTurn):
        model.__table__.create(engine)
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

    first = owner_turn("Review the product specialist report", specialist_schedule_id=schedule_id)
    assert first["evidence"]["evidence_class"] == "INTERNAL_ADVISORY"
    assert first["evidence"]["verified_internal_outcome_ids"] == []
    next_cadence = client.get(f"{schedule_root}/{schedule_id}").json()["next_due_at"]
    unrelated_advice = client.get(f"{schedule_root}/{other_schedule_id}").json()["latest_report"]

    assert client.post(f"{FACTORY}/listing-drafts", headers=admin, json={
        **listing, "prime_verdict_id": str(uuid4()),
    }).status_code == 409
    artifact = client.post(f"{PHASE3}/review-artifact", json=proposal).json()
    queued = client.post("/loki/reviews", json={**artifact, "input_source": "prime-product-rehearsal"})
    assert queued.status_code == 201, queued.text
    review_id = queued.json()["id"]
    review = client.get("/loki/worker/reviews", headers=worker).json()[0]
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
    executed = client.post(f"{FACTORY}/actions/run-once", headers=admin).json()
    assert executed["status"] == "completed"
    assert executed["receipt"]["sales_verified"] is False
    assert executed["receipt"]["authority_mode"] == "STANDING_MANDATE"
    assert executed["receipt"]["product_asset"]["sha256"] == checksum
    assert executed["receipt"]["prime_decision"]["review_id"] == review_id
    assert executed["receipt"]["prime_decision"]["verdict_id"] == listing["prime_verdict_id"]
    with Session(engine) as db:
        listing_record = db.get(MediaContent, executed["receipt"]["media_content_id"])
        assert json.loads(listing_record.body)["product_asset"]["sha256"] == checksum
        assert json.loads(listing_record.body)["purchase_url"] is None
    assert client.get(f"{FACTORY}/actions/{action_id}", headers=admin).json()["internal_artifact_verified"]

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
    follow_up = owner_turn("What did we learn after the internal draft?", specialist_schedule_id=schedule_id)
    assert follow_up["evidence"]["verified_internal_outcome_ids"] == [report["trigger_outcome_event_id"]]
    assert len(client.get(turns).json()) == 3
    assert client.get(f"{schedule_root}/{other_schedule_id}").json()["latest_report"] == unrelated_advice
    with Session(engine) as db:
        assert run_due_schedule(db, now=slot_time + timedelta(seconds=1)) == {"status": "idle"}

    pending_id = submit_and_approve({**listing, "request_key": "workshop-listing-02"})
    with Session(engine) as db:
        db.get(ProductArtifact, UUID(asset_id)).data = b"Bad storage bytes"
        db.commit()
    assert client.get(download_url, headers=owner).status_code == 409
    blocked = client.post(f"{FACTORY}/actions/run-once", headers=admin).json()
    assert blocked["action_id"] == pending_id
    assert blocked["reason"] == "Internal product artifact integrity mismatch"

    assert client.delete(f"{ASSETS}/{asset_id}", headers=admin).status_code == 401
    assert client.delete(f"{ASSETS}/{asset_id}", headers=owner).json()["revoked"]
    revoked_run = client.post(f"{FACTORY}/actions/run-once", headers=admin).json()
    assert revoked_run["action_id"] == pending_id
    assert revoked_run["reason"] == "Internal product artifact revoked"
    with Session(engine) as db:
        assert db.query(MediaContent).count() == 1
        learned = db.query(LegacyOrchestrationEvent).filter_by(event_type="MIMIR_INTERNAL_ARTIFACT_VERIFIED").one()
        verified = json.loads(learned.payload_json)
        assert verified["product_asset"]["sha256"] == checksum
        assert verified["prime_decision"]["proposal_sha256"] == artifact["artifact_sha256"]
