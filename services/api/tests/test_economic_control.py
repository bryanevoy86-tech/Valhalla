"""End-to-end economic rehearsal through Prime, existing Loki, and Pantheon."""
from datetime import date, datetime, timedelta, timezone
import json
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.loki.analyst import challenge
from app.loki.models import LokiFinding, LokiIndependentReceipt, LokiReconsideration, LokiReview
from app.models.completion_registry import LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent
from app.models.economic_control import EconomicOperation, EconomicPool, EconomicRecord
from app.models.revenue_ledger import RevenueLedger
from app.models.specialist_assignment import SpecialistAssignment, SpecialistTrigger
from app.pantheon.monitor import run_assignment
from app.routers import economic_control
from app.services.economic_control import require_no_containment
from app.services.owner_operating_brief import operating_evidence, owner_attention

ROOT = "/api/prime/economy"
OWNER = {"X-Owner-Mandate-Key": "economy-isolated-owner"}
REVIEWER = {"X-Loki-Reviewer-Key": "economy-independent-reviewer"}
SCOPE = {"legacy_instance_id": "sandbox-legacy", "business_id": "venture-local",
         "engine_id": "candidate-engine", "jurisdiction": "CA-MB"}
MIRROR = {**SCOPE, "legacy_instance_id": "sandbox-mirror", "jurisdiction": "CA-ON"}


@pytest.fixture
def economic_client(deal_client, monkeypatch):
    client, engine = deal_client
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", OWNER["X-Owner-Mandate-Key"])
    monkeypatch.setenv("VALHALLA_LOKI_REVIEWER_KEY", REVIEWER["X-Loki-Reviewer-Key"])
    monkeypatch.setenv("VALHALLA_LOKI_REVIEWER_ID", "economic-independent-fixture")
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    for model in (LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent, EconomicOperation,
                  EconomicPool, EconomicRecord, RevenueLedger, SpecialistAssignment, SpecialistTrigger, LokiReview, LokiFinding,
                  LokiIndependentReceipt, LokiReconsideration):
        model.__table__.create(engine)
    with Session(engine) as db:
        db.add(EconomicPool(currency="CAD"))
        db.add(EconomicPool(currency="USD"))
        for scope in (SCOPE, MIRROR):
            db.add(LegacyInstanceRegistryItem(
                legacy_instance_id=scope["legacy_instance_id"], display_name="Economic rehearsal", status="PASS",
                synchronization_status="SYNCED", engines_json='["candidate-engine","other-engine"]',
                assigned_businesses_json='["venture-local"]', assigned_jurisdictions_json=json.dumps([scope["jurisdiction"]]),
                local_knowledge_context_json=json.dumps(scope),
            ))
        db.commit()
    return client, engine


def post(client, endpoint, data, code=201):
    response = client.post(f"{ROOT}/{endpoint}", headers=OWNER, json=data)
    assert response.status_code == code, response.text
    return response.json()


def mandate(today, **overrides):
    return {"id": str(uuid4()), "scope": SCOPE, "currency": "CAD", "max_exposure": 500,
            "max_cumulative_loss": 100, "max_additional_funding": 200, "min_operating_reserve": 200,
            "review_by": (today + timedelta(days=20)).isoformat(), "minimum_period_net": 0,
            "continuation_criteria": "Maintain positive operating cash.", "suspension_criteria": "Stop at the loss ceiling.",
            "exit_criteria": "Preserve reusable assets and retire the strategy.",
            "obligations": ["Verify licensing", "Review insurance", "Check bond and contracts"], **overrides}


def performance(today, **overrides):
    return {"id": str(uuid4()), "scope": SCOPE, "start": today.isoformat(), "end": today.isoformat(),
            "operating_receipts": 100, "operating_costs": 50, "outstanding_exposure": 20,
            "uncommitted_local_cash": 450, "receipt_ref": f"fixture:{uuid4()}", "obligations_status": "SATISFIED",
            "evidence_class": "RECONCILIATION_FIXTURE", **overrides}


def liquidity(today, **overrides):
    return {"id": str(uuid4()), "scope": SCOPE, "as_of": today.isoformat(), "receipt_ref": f"fixture:{uuid4()}",
            "unrestricted_pool_minor": 170, "protected_pool_minor": 10000,
            "evidence_class": "RECONCILIATION_FIXTURE", **overrides}


def option(today, key, **overrides):
    return {"id": str(uuid4()), "scope": SCOPE, "opportunity_key": key, "title": f"Candidate {key}",
            "origin": "NEW_DISCOVERY", "status": "CANDIDATE", "evidence_ref": "fixture:demand-ledger",
            "valid_through": (today + timedelta(days=14)).isoformat(), "required_capital": 120,
            "projected_annual_net": 1800, "maximum_downside": 70, "uncertainty_bp": 1500, "demand_bp": 8500,
            "operational_independence_bp": 8000, "time_to_revenue_days": 30,
            "compliance": "SATISFIED_IN_FIXTURE", "dependencies": [], "activation_requirements": ["Owner mandate"], **overrides}


def plan(**overrides):
    return {"id": str(uuid4()), "scope": SCOPE, "action": "EXPAND", "requested_additional_minor": 120,
            "rationale": "Rehearse only within the declared exposure limits.", "past_spend_minor": 0, "assets": [], **overrides}


def queue_review(client, proposal, *, reconsider):
    artifact = post(client, "review-artifact", proposal, 200)
    queued = client.post("/loki/reviews", json=artifact)
    assert queued.status_code == 201, queued.text
    review_id = queued.json()["id"]
    queue = client.get("/loki/worker/reviews", headers=REVIEWER, params={"artifact_type": "economic_advice"})
    item = next(data for data in queue.json() if data["review_id"] == review_id)
    independent = challenge(item).model_dump(mode="json")
    published = client.post(f"/loki/worker/reviews/{review_id}/result", headers=REVIEWER, json=independent)
    assert published.status_code == 201, published.text
    if reconsider:
        findings = client.get(f"/loki/reviews/{review_id}/findings").json()
        response = client.post(f"/loki/reviews/{review_id}/reconsider", headers=OWNER, json={
            "artifact_sha256": artifact["artifact_sha256"], "disposition": "accept_risk",
            "material_finding_ids": [data["id"] for data in findings],
            "reason": "Reviewed the scoped fixture and confirmed this is internal and reversible.",
        })
        assert response.status_code == 200, response.text
    return {"plan": proposal, "independent_review_id": review_id,
            "expected_artifact_sha256": artifact["artifact_sha256"]}, independent


def test_redeploy_then_contain_and_preserve_reusable_assets(economic_client, monkeypatch):
    client, engine = economic_client
    clock = [datetime.now(timezone.utc) - timedelta(days=2)]
    monkeypatch.setattr(economic_control, "now", lambda: clock[0])
    today = clock[0].date()

    initial = mandate(today)
    post(client, "mandates", initial)
    assert "MISSING_OR_STALE_PERFORMANCE" in post(client, "assessment", SCOPE, 200)["blockers"]
    catalog = client.get(f"{ROOT}/historical-candidates").json()
    assert any(item["engine_id"] == "wholesaling" for item in catalog["candidates"])
    assert catalog["mandatory_startup_engines"] == []
    post(client, "opportunities", option(today, "wholesaling", origin="HISTORICAL_PLAYBOOK", status="OPERATING_REPORTED", projected_annual_net=700))
    post(client, "opportunities", option(today, "discovered-service"))
    post(client, "opportunities", option(today, "blocked-bonus", compliance="BLOCKED", projected_annual_net=100000))
    post(client, "liquidity", liquidity(today))
    healthy = performance(today)
    post(client, "performance", healthy)
    evaluation = post(client, "assessment", SCOPE, 200)
    assert evaluation["period_net_minor"] == 50
    assert evaluation["suggested_action"] == "REDEPLOY"
    assert evaluation["alternatives"][0]["opportunity_key"] == "discovered-service"
    assert evaluation["alternatives"][-1]["blockers"] == ["COMPLIANCE"]
    assert evaluation["alternatives"][1]["foregone_best_alternative_minor"] > 0

    proposal = plan(action="REDEPLOY", alternative_key="discovered-service")
    unsigned, _ = queue_review(client, proposal, reconsider=False)
    post(client, "decisions", unsigned, 409)
    reviewed, _ = queue_review_again(client, unsigned)
    result = post(client, "decisions", reviewed)
    assert result["reserved_simulation_minor"] == 120 and result["execution_authorized"] is False
    assert post(client, "decisions", reviewed) == result

    for role in ("NJORD", "NORNS", "LOKI", "TYR", "ODIN", "MIMIR"):
        enrolled = client.post("/api/prime/pantheon/assignments", headers=OWNER, json={
            **SCOPE, "assignment_id": str(uuid4()), "role": role, "cadence_seconds": 300, "duration_seconds": 600,
        })
        assert enrolled.status_code == 201, enrolled.text

    clock[0] += timedelta(days=1)
    bad = performance(clock[0].date(), operating_receipts=0, operating_costs=100, obligations_status="BREACHED")
    post(client, "performance", bad)
    with Session(engine) as db:
        assert run_assignment(db, "NJORD")["status"] == "observed"
    assert post(client, "assessment", SCOPE, 200)["suggested_action"] == "EXIT"
    # A new mandate ID cannot wipe the loss, increase caps, or migrate it to another engine.
    post(client, "mandates", mandate(today, previous_id=initial["id"], max_cumulative_loss=101), 409)
    post(client, "mandates", mandate(today, scope={**SCOPE, "engine_id": "other-engine"}), 409)
    post(client, "mandates", mandate(today, currency="USD"), 409)
    post(client, "mandates", mandate(today, previous_id=initial["id"]))
    bad_plan = plan(past_spend_minor=400, cross_business_support=True)
    request, independent = queue_review(client, bad_plan, reconsider=False)
    assert {"sunk_cost", "loss_limit_bypass", "authority"} <= {item["category"] for item in independent["findings"]}
    denial = post(client, "decisions", request, 409)
    assert "CUMULATIVE_LOSS_LIMIT" in denial["detail"]["blockers"]

    software = {"asset_ref": "fixture:software", "kind": "SOFTWARE",
                "rights": "REUSE_PERMITTED", "projected_liquidation_minor": 75, "obligations": []}
    pledged = {**software, "asset_ref": "fixture:pledged", "rights": "ENCUMBERED"}
    exit_plan = plan(action="EXIT", requested_additional_minor=0, assets=[software, pledged])
    exit_review, _ = queue_review(client, exit_plan, reconsider=True)
    receipt = post(client, "decisions", exit_review)
    assert receipt["reuse_candidates"] == [software] and receipt["actual_recovered_capital_minor"] is None
    with Session(engine) as db:
        event = run_assignment(db, "MIMIR")["report_event_id"]
        assert db.query(RevenueLedger).count() == 0
        assert db.get(EconomicPool, "CAD").committed_minor == 120
        [alert] = operating_evidence(db)["latest_economic_alerts"]
        assert alert["scope"] == SCOPE and alert["suggested_action"] == "EXIT"
        with pytest.raises(HTTPException, match="Economic containment"):
            require_no_containment(db, SCOPE)
    obs = client.get(f"/api/prime/pantheon/reports/{event}").json()
    assert obs["trigger"] == "ECONOMIC_REASSESSMENT"
    learned = obs["observations"]["economic_reassessment"]
    assert learned["last_internal_decision"]["action"] == "EXIT"
    assert learned["verified_real_world_outcome"] is False


def queue_review_again(client, unsigned):
    review_id = unsigned["independent_review_id"]
    findings = client.get(f"/loki/reviews/{review_id}/findings").json()
    response = client.post(f"/loki/reviews/{review_id}/reconsider", headers=OWNER, json={
        "artifact_sha256": unsigned["expected_artifact_sha256"], "disposition": "accept_risk",
        "material_finding_ids": [data["id"] for data in findings], "reason": "Accept only the bounded rehearsal.",
    })
    assert response.status_code == 200, response.text
    return unsigned, findings


def test_reserves_conflicts_replay_and_emergency_stop(economic_client, monkeypatch):
    client, engine = economic_client
    today = datetime.now(timezone.utc).date()
    post(client, "mandates", mandate(today))
    post(client, "mandates", mandate(today, scope=MIRROR))
    perf = performance(today)
    post(client, "performance", perf)
    post(client, "performance", {**perf, "id": str(uuid4()), "scope": MIRROR}, 409)
    post(client, "performance", performance(today, scope=MIRROR))
    post(client, "liquidity", liquidity(today - timedelta(days=8)))
    assert "MISSING_OR_STALE_LIQUIDITY" in post(client, "assessment", SCOPE, 200)["blockers"]
    snapshot = liquidity(today)
    post(client, "liquidity", snapshot)
    primary, _ = queue_review(client, plan(), reconsider=True)
    competing, _ = queue_review(client, plan(scope=MIRROR), reconsider=True)
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    post(client, "decisions", primary, 503)
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    post(client, "decisions", primary)
    post(client, "decisions", competing, 409)
    scarce = post(client, "assessment", MIRROR, 200)
    assert scarce["new_exposure_available_minor"] == 50
    too_large, _ = queue_review(client, plan(scope=MIRROR, requested_additional_minor=51), reconsider=False)
    blocked = post(client, "decisions", too_large, 409)
    assert "PROTECTED_RESERVE_OR_UNAVAILABLE_FUNDS" in blocked["detail"]["blockers"]
    post(client, "liquidity", liquidity(today, scope=MIRROR, unrestricted_pool_minor=10000))
    assert "CONFLICTING_LIQUIDITY" in post(client, "assessment", MIRROR, 200)["blockers"]
    with Session(engine) as db:
        item = db.get(EconomicRecord, UUID(perf["id"]))
        item.payload = {**item.payload, "operating_costs": 1}
        db.commit()
    post(client, "assessment", SCOPE, 409)


def test_immediate_containment_holds_existing_factory_lane(economic_client, monkeypatch):
    from app.models.media_engine import MediaContent
    from app.services.prime_business_execution import run_one_approved_draft

    client, engine = economic_client
    MediaContent.__table__.create(engine)
    monkeypatch.setenv("VALHALLA_FACTORY_KEY", "economic-factory-test")
    headers = {**OWNER, "X-Business-Factory-Key": "economic-factory-test"}
    today = datetime.now(timezone.utc).date()
    post(client, "mandates", mandate(today))
    factory = "/api/business-factory"
    listing = {
        **SCOPE, "product_id": "candidate_product", "industry": "digital_products",
        "title": "Scoped internal product", "description": "Candidate for a private economic containment rehearsal.",
        "price_cents_cad": 600, "request_key": "econ-contained-fixture",
    }
    created = client.post(f"{factory}/listing-drafts", headers=headers, json=listing)
    assert created.status_code == 200, created.text
    action_id = created.json()["action_id"]
    approve = client.post(f"/api/business-factory/actions/{action_id}/approve",
                          headers=headers, json={"confirmation": "APPROVE_INTERNAL_DRAFT"})
    assert approve.status_code == 200, approve.text
    pending = client.post(f"{factory}/listing-drafts", headers=headers,
                          json={**listing, "request_key": "queued-before-containment"})
    assert pending.status_code == 200, pending.text
    pending_id = pending.json()["action_id"]
    draft_mandate = {**SCOPE, "mandate_id": "previously-open-fixture", "product_id": "candidate_product",
                     "ttl_seconds": 600, "max_uses": 1, "max_price_cents_cad": 600}
    assert client.post(f"{factory}/mandates", headers=headers, json=draft_mandate).status_code == 200
    freeze = {"id": str(uuid4()), "scope": SCOPE, "rationale": "Stop further commitments until the issue is understood."}
    assert client.post(f"{ROOT}/containment", json=freeze).status_code == 401
    receipt = post(client, "containment", freeze)
    assert post(client, "containment", freeze) == receipt
    denied_submission = client.post(f"{factory}/listing-drafts", headers=headers,
                                    json={**listing, "request_key": "new-held-work"})
    assert denied_submission.status_code == 409 and "containment" in denied_submission.json()["detail"]
    replay = client.post(f"{factory}/listing-drafts", headers=headers, json=listing)
    assert replay.status_code == 200 and replay.json()["duplicate"] is True
    assert replay.json()["action_id"] == action_id
    denied = client.post(f"{factory}/actions/{pending_id}/approve", headers=headers,
                         json={"confirmation": "APPROVE_INTERNAL_DRAFT"})
    assert denied.status_code == 409 and "containment" in denied.json()["detail"]
    denied_grant = client.post(f"{factory}/mandates", headers=headers,
                               json={**draft_mandate, "mandate_id": "contained-fixture"})
    assert denied_grant.status_code == 409 and "containment" in denied_grant.json()["detail"]
    assert client.get(f"{factory}/actions/{pending_id}", headers=headers).status_code == 200
    assert client.post(f"{factory}/mandates/{draft_mandate['mandate_id']}/revoke", headers=headers).status_code == 200
    with Session(engine) as db:
        from app.services.prime_business_execution import _approval_id, _mandate_event_id

        assert db.query(LegacyInstanceWorkItem).count() == 2
        assert db.query(LegacyOrchestrationEvent).filter_by(event_type="FACTORY_WORK_QUEUED").count() == 2
        assert db.query(LegacyOrchestrationEvent).filter_by(event_id=_approval_id(pending_id)).count() == 0
        assert db.query(LegacyOrchestrationEvent).filter_by(event_id=_mandate_event_id("contained-fixture")).count() == 0
        outcome = run_one_approved_draft(db)
        assert outcome["status"] == "blocked" and "containment" in outcome["reason"]
        assert db.query(MediaContent).count() == 0


def test_foundry_comparison_uses_scoped_evidence_and_immutable_opening_history(economic_client):
    from app.models.foundry_evidence import FoundryEvidence

    client, engine = economic_client
    FoundryEvidence.__table__.create(engine)
    today = datetime.now(timezone.utc).date()
    initial = mandate(today, opening_cumulative_loss=12, opening_additional_funding=10,
                      opening_receipt_ref="fixture:prior-periods")
    post(client, "mandates", initial)
    post(client, "mandates", {**initial, "id": str(uuid4()), "previous_id": initial["id"]}, 409)
    post(client, "performance", performance(today))
    post(client, "liquidity", liquidity(today))
    intake = {
        **SCOPE, "evidence_id": str(uuid4()), "kind": "SERVICE", "evidence_class": "SIMULATION",
        "title": "Rehearsed demand study", "source_ref": "fixture:demand", "observed_on": today.isoformat(),
        "expires_on": (today + timedelta(days=6)).isoformat(), "currency": "CAD", "unit_price": 50,
        "variable_cost_per_unit": 20, "acquisition_cost_per_unit": 0, "monthly_fixed_cost": 130,
        "monthly_units": 10, "startup_capital": 140, "test_cost": 0,
        "rights_attestation": "AUTHORIZED_INTERNAL_RESEARCH",
    }
    source_response = client.post("/api/prime/foundry/evidence", headers=OWNER, json=intake)
    assert source_response.status_code == 201, source_response.text
    post(client, "opportunities", option(today, "foundry-option", origin="FOUNDRY",
         foundry_evidence_id=intake["evidence_id"], projected_annual_net=99999))
    snapshot = post(client, "assessment", SCOPE, 200)
    candidate = snapshot["alternatives"][0]
    assert candidate["required_capital"] == 140
    assert candidate["projected_annual_net"] == 2040
    assert snapshot["cumulative_loss_minor"] == 12 and snapshot["pool_committed_minor"] == 10
    client.delete(f"/api/prime/foundry/evidence/{intake['evidence_id']}", headers=OWNER)
    assert "FOUNDRY_SOURCE_UNAVAILABLE" in post(client, "assessment", SCOPE, 200)["alternatives"][0]["blockers"]


def test_reviewed_restart_releases_reservations_without_restoring_lifetime_limits(economic_client, monkeypatch):
    client, engine = economic_client
    clock = [datetime.now(timezone.utc) - timedelta(days=3)]
    monkeypatch.setattr(economic_control, "now", lambda: clock[0])
    today = clock[0].date()
    post(client, "mandates", mandate(today))
    post(client, "performance", performance(today))
    post(client, "liquidity", liquidity(today))
    expansion, _ = queue_review(client, plan(), reconsider=True)
    reservation = post(client, "decisions", expansion)
    release = {"id": str(uuid4()), "scope": SCOPE, "decision_id": reservation["id"],
               "reason": "CANCELLED", "evidence_ref": "fixture:cancel-prelaunch"}
    result = post(client, "reservation-releases", release)
    assert post(client, "reservation-releases", release) == result
    assert result["released_simulation_minor"] == 120 and not result["cumulative_budget_restored"]
    post(client, "reservation-releases", {**release, "id": str(uuid4())}, 409)
    totals = client.get(f"{ROOT}/portfolio-exposure", headers=OWNER).json()["totals"]
    assert next(item for item in totals if item["currency"] == "CAD")["outstanding_reservations_minor"] == 0
    assessment = post(client, "assessment", SCOPE, 200)
    assert assessment["simulated_funding_minor"] == 120 and assessment["comparison_budget_minor"] == 80

    post(client, "containment", {"id": str(uuid4()), "scope": SCOPE, "rationale": "Freeze launch while reviewing coverage."})
    with Session(engine) as db:
        mirror = db.query(LegacyInstanceRegistryItem).filter_by(legacy_instance_id=MIRROR["legacy_instance_id"]).one()
        mirror.parent_instance_id = SCOPE["legacy_instance_id"]
        db.commit()
    with Session(engine) as db, pytest.raises(HTTPException, match="containment"):
        require_no_containment(db, MIRROR)
    restart = plan(action="RESTART", requested_additional_minor=0)
    preview = post(client, "review-artifact", restart, 200)
    assert "RESTART_REQUIRES_POST_CONTAINMENT_PERFORMANCE" in preview["raw_input"]["analysis"]["blockers"]
    clock[0] += timedelta(days=1)
    post(client, "performance", performance(clock[0].date()))
    obligation = {"id": str(uuid4()), "scope": SCOPE, "obligation_key": "coverage-renewal",
                  "due_on": clock[0].date().isoformat(), "status": "OPEN", "amount_minor": 35,
                  "evidence_ref": "fixture:pending-coverage"}
    post(client, "obligations", obligation)
    blocked = post(client, "review-artifact", restart, 200)["raw_input"]["analysis"]["blockers"]
    assert "TRACKED_OBLIGATIONS_UNRESOLVED" in blocked
    post(client, "obligations", {**obligation, "id": str(uuid4()), "previous_id": obligation["id"],
                                 "status": "CLOSED_IN_FIXTURE", "evidence_ref": "fixture:reviewed-coverage"})
    reviewed, _ = queue_review(client, restart, reconsider=True)
    receipt = post(client, "decisions", reviewed)
    assert receipt["action"] == "RESTART" and not receipt["execution_authorized"]
    with Session(engine) as db:
        require_no_containment(db, SCOPE)
        require_no_containment(db, MIRROR)


def test_discovery_queue_sources_rank_and_do_not_claim_external_demand(economic_client, monkeypatch):
    from app.models.completion_registry import KnowledgeRegistryItem, LearningFeedbackRecord, SourceRegistryItem
    from app.models.foundry_evidence import FoundryEvidence
    from app.models.foundry_intake import FoundryIntakeJob
    from app.services import foundry_intake
    from sqlalchemy.exc import OperationalError

    client, engine = economic_client
    for model in (KnowledgeRegistryItem, LearningFeedbackRecord, SourceRegistryItem, FoundryEvidence, FoundryIntakeJob):
        model.__table__.create(engine)
    with Session(engine) as db:
        db.add(SourceRegistryItem(source_id="regional-buyer-sample", source_type="DEMAND_EXPORT",
                                  canonical_name="Buyer sample fixture", data_class="synthetic",
                                  jurisdiction="CA-MB", terminal_state="PASS", mode_allowlist_json='["practice"]',
                                  freshness_sla_hours=72))
        db.commit()
    at = foundry_intake.current_time()
    today = at.date()
    post(client, "mandates", mandate(today, max_additional_funding=500))
    post(client, "performance", performance(today))
    post(client, "liquidity", liquidity(today, unrestricted_pool_minor=450))
    post(client, "opportunities", option(today, "old-playbook", projected_annual_net=400))
    assignment = client.post("/api/prime/pantheon/assignments", headers=OWNER, json={
        **SCOPE, "assignment_id": str(uuid4()), "role": "ODIN", "cadence_seconds": 600, "duration_seconds": 3600,
    })
    assert assignment.status_code == 201, assignment.text
    with Session(engine) as db:
        run_assignment(db, "ODIN")  # Consume the scheduled assessment, leaving an explicit discovery wake-up.
    evidence = {
        **SCOPE, "evidence_id": str(uuid4()), "kind": "OTHER", "revenue_model": "RECURRING",
        "evidence_class": "SIMULATION", "title": "Mobile tool calibration service",
        "source_ref": "https://web.gov.mb.ca/DisclosureOfContracts/", "observed_on": today.isoformat(),
        "expires_on": (today + timedelta(days=3)).isoformat(), "currency": "CAD",
        "unit_price": 50, "variable_cost_per_unit": 10, "acquisition_cost_per_unit": 10,
        "monthly_fixed_cost": 75, "monthly_units": 10, "startup_capital": 120, "test_cost": 8,
        "rights_attestation": "AUTHORIZED_INTERNAL_RESEARCH",
    }
    job = {"evidence": evidence, "source_id": "regional-buyer-sample", "external_key": "CalibrationSurvey",
           "adapter": "DEMAND_EXPORT", "buyer_segment": "Synthetic independent repair shops",
           "sample_count": 40, "demand_count": 24}
    url = "/api/prime/foundry/intake"
    stale = {**evidence, "observed_on": (today - timedelta(days=5)).isoformat()}
    assert client.post(url, headers=OWNER, json={**job, "evidence": stale}).status_code == 409
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    publisher = Ed25519PrivateKey.generate()
    key_url = f"{url}/sources/{job['source_id']}/signing-key"
    key = {"public_key_hex": publisher.public_key().public_bytes_raw().hex()}
    assert client.put(key_url, json=key).status_code == 401
    assert client.put(key_url, headers=OWNER, json=key).status_code == 200
    assert client.post(url, headers=OWNER, json=job).status_code == 409
    job["source_signed_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    def signed(values):
        return {**values, "source_signature": publisher.sign(foundry_intake.source_signature_message(values)).hex()}
    expired = signed({**job, "source_signed_at": (datetime.now(timezone.utc) - timedelta(hours=1))
                      .isoformat().replace("+00:00", "Z")})
    assert client.post(url, headers=OWNER, json=expired).status_code == 409
    job = signed(job)
    assert client.post(url, headers=OWNER, json={**job, "sample_count": 80}).status_code == 409
    queued = client.post(url, headers=OWNER, json=job)
    assert queued.status_code == 202, queued.text
    assert client.post(url, headers=OWNER, json=job).json() == queued.json()
    duplicate = {**evidence, "evidence_id": str(uuid4())}
    assert client.post(url, headers=OWNER, json=signed({**job, "evidence": duplicate,
                                                       "external_key": "calibrationsurvey"})).status_code == 409
    original = foundry_intake.materialize
    def unavailable(*args):
        raise OperationalError("fixture", None, Exception())
    monkeypatch.setattr(foundry_intake, "materialize", unavailable)
    with Session(engine) as db:
        state = foundry_intake.run_intake(db, now=at + timedelta(seconds=10))
        assert state["error_code"] == "ADAPTER_RETRY_PENDING" and state["attempts"] == 1
        assert foundry_intake.run_intake(db, now=at + timedelta(seconds=15)) == {"status": "idle"}
    monkeypatch.setattr(foundry_intake, "materialize", original)
    with Session(engine) as db:
        state = foundry_intake.run_intake(db, now=at + timedelta(minutes=4))
        assert state["status"] == "COMPLETED" and state["attempts"] == 2
        report_id = run_assignment(db, "ODIN", now=at + timedelta(minutes=4))["report_event_id"]
    report = client.get(f"/api/prime/pantheon/reports/{report_id}").json()
    assert report["trigger"] == "SOURCE_DISCOVERY"
    candidate = client.get(f"/api/prime/foundry/reports/{report_id}/candidate/{evidence['evidence_id']}")
    assert candidate.status_code == 200, candidate.text
    proposal = candidate.json()["proposal"]
    assert proposal["revenue_type"] == "RECURRING"
    assert proposal["specialist_inputs"]["discovery_demand"]["sample_demand_bp"] == 6000
    recommendation = client.post("/api/completion/phase3/universal-opportunity/evaluate",
                                 json={"opportunities": [proposal], "shadow_mode": True})
    assert recommendation.status_code == 200, recommendation.text
    post(client, "opportunities", option(today, "mobile-calibration", origin="FOUNDRY",
                                         foundry_evidence_id=evidence["evidence_id"], demand_bp=9999))
    result = post(client, "assessment", SCOPE, 200)["alternatives"][0]
    assert result["opportunity_key"] == "mobile-calibration" and result["demand_bp"] == 6000
    review, _ = queue_review(client, plan(action="REDEPLOY", alternative_key="mobile-calibration"), reconsider=True)
    approved = post(client, "decisions", review)
    assert approved["observed"]["alternatives"][0]["demand_evidence"]["independently_validated"] is False
    assert approved["execution_authorized"] is False
    assert approved["observed"]["opportunity_selection"]["first_research_candidate_key"] == "mobile-calibration"
    assert approved["observed"]["alternatives"][0]["ranking_basis"]["verified_monthly_owner_income_minor"] is None
    sources = {
        "fleet-subscription": ("SAAS", "SUBSCRIPTION", 80, "SATISFIED_IN_FIXTURE",
                               "https://publications.gc.ca/collections/collection_2025/rncan-nrcan/M144-294-2025-eng.pdf"),
        "shop-acquisition": ("ACQUISITION", "ACQUISITION", 100, "UNRESOLVED",
                             "https://www.bdc.ca/en/articles-tools/start-buy-business/buy-business/buying-business-conducting-due-diligence"),
    }
    for key, (kind, model, price, compliance, citation) in sources.items():
        new_source = {**job["evidence"], "evidence_id": str(uuid4()), "kind": kind, "revenue_model": model,
                      "source_ref": citation, "unit_price": price, "title": key}
        intake_response = client.post(url, headers=OWNER, json=signed({
            **job, "source_signed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "evidence": new_source, "external_key": key,
        }))
        assert intake_response.status_code == 202, intake_response.text
        with Session(engine) as db:
            assert foundry_intake.run_intake(db)["status"] == "COMPLETED"
        post(client, "opportunities", option(today, key, origin="FOUNDRY", compliance=compliance,
             foundry_evidence_id=new_source["evidence_id"]))

    # An enticing, declaration-only projection can rank highly in the fixture
    # without becoming the next research candidate, let alone a business selection.
    post(client, "opportunities", option(today, "unverified-promise", projected_annual_net=90000))
    ranked = post(client, "assessment", SCOPE, 200)
    selection = ranked["opportunity_selection"]
    assert ranked["best_eligible_alternative_key"] == "unverified-promise"
    assert selection["decision"] == "RESEARCH_ONLY"
    assert selection["first_research_candidate_key"] == "fleet-subscription"
    assert selection["commercial_selection_key"] is None
    assert selection["verified_monthly_owner_income_minor"] is None
    evidence_by_key = {row["opportunity_key"]: row for row in ranked["alternatives"]}
    assert "ACQUISITION_TERMS_MISSING" in evidence_by_key["shop-acquisition"]["blockers"]
    assert "COMPLIANCE" in evidence_by_key["shop-acquisition"]["blockers"]
    assert evidence_by_key["fleet-subscription"]["foundry_source"]["citation"] == sources["fleet-subscription"][4]

    advice = plan(action="CONTINUE", requested_additional_minor=0)
    request, result = queue_review(client, advice, reconsider=False)
    assert "opportunity_ranking_evidence" in {finding["category"] for finding in result["findings"]}
    denied = post(client, "decisions", request, 409)
    assert "Exact independent Loki review" in denied["detail"]
    snapshot = post(client, "review-artifact", advice, 200)
    accepted_request, _ = queue_review_again(client, request)
    recorded = post(client, "decisions", accepted_request)
    assert recorded["observed"]["opportunity_selection"] == selection
    assert recorded["artifact_sha256"] == snapshot["artifact_sha256"]
    assert recorded["reserved_simulation_minor"] == 0 and not recorded["execution_authorized"]
    readback = client.get(f"{ROOT}/records/{advice['id']}")
    assert readback.status_code == 200
    assert readback.json()["data"] == recorded

    from app.services.economic_control import specialist_economics

    with Session(engine) as db:
        for role in ("NORNS", "ODIN", "HEIMDALL"):
            observation = specialist_economics(db, role, SCOPE, today)["economic_reassessment"]
            assert observation["opportunity_selection"] == selection
        learning = specialist_economics(db, "MIMIR", SCOPE, today)["economic_reassessment"]
        assert learning["last_internal_decision"] == recorded
        assert learning["verified_real_world_outcome"] is False
    alternate = snapshot["raw_input"]
    alternate["analysis"]["opportunity_selection"]["first_research_candidate_key"] = "unverified-promise"
    from app.loki.evidence import artifact_digest

    artifact_type = snapshot["artifact_type"]
    ref = snapshot["heimdall_reference_id"]
    check = challenge({"artifact_type": artifact_type, "reference": ref, "raw_input": alternate,
                       "artifact_sha256": artifact_digest(artifact_type, ref, alternate)})
    assert any(f.category == "opportunity_ranking_conflict" and f.severity == "critical" for f in check.findings)
    print("OPPORTUNITY_COMPARISON " + json.dumps({
        "decision_id": advice["id"], "artifact_sha256": recorded["artifact_sha256"],
        "review_id": recorded["independent_review_id"], "selection": selection,
        "scores": {key: row["adjusted_forward_value_minor"] for key, row in evidence_by_key.items()},
    }, sort_keys=True))

    with monkeypatch.context() as stopped:
        stopped.setenv("VALHALLA_EMERGENCY_STOP", "true")
        held = post(client, "assessment", SCOPE, 200)["opportunity_selection"]
        assert held["decision"] == "ABSTAIN" and "EMERGENCY_STOP" in held["scope_holds"]
    with Session(engine) as db:
        db.query(SourceRegistryItem).filter_by(source_id="regional-buyer-sample").one().active = False
        db.commit()
    assert client.get(f"/api/prime/foundry/reports/{report_id}/candidate/{evidence['evidence_id']}").status_code == 409
    revoked = post(client, "assessment", SCOPE, 200)["opportunity_selection"]
    assert revoked["decision"] == "ABSTAIN"
    assert revoked["first_research_candidate_key"] is None


def test_statement_continuity_quarantine_and_fixture_asset_recovery(economic_client, monkeypatch):
    from app.finops.models import VaultBalance
    from app.models.treasury_reconciliation import StatementAccount, StatementEntry, StatementImport

    client, engine = economic_client
    for model in (StatementAccount, StatementEntry, StatementImport, VaultBalance):
        model.__table__.create(engine)
    today = datetime.now(timezone.utc).date()
    earlier = today - timedelta(days=1)
    from app.routers import floor_control

    class PreviousLocalDay(date):
        @classmethod
        def today(cls):
            return earlier

    monkeypatch.setattr(floor_control, "date", PreviousLocalDay)
    with Session(engine) as db:
        db.add(VaultBalance(vault_code="MAIN", balance=987, currency="CAD", last_source="fx_engine"))
        db.commit()
    root = "/api/governance/floor/treasury"
    audit = client.get(f"{root}/legacy-vault-audit", headers=OWNER).json()
    assert audit["quarantined"][0]["recorded_unreconciled_amount"] == "987.0"

    row = {"external_ref": "opening-expense", "posted_on": earlier.isoformat(), "amount_minor": -80, "category": "EXPENSE"}
    statement = {"id": str(uuid4()), "scope": SCOPE, "source_id": "LocalBankFixture",
                 "account_ref": "business-a", "purpose": "BUSINESS", "currency": "CAD",
                 "start": earlier.isoformat(), "end": earlier.isoformat(), "opening_minor": 500, "closing_minor": 420,
                 "outstanding_liabilities_minor": 20, "expense_budget_minor": 65, "entries": [row],
                 "basis": "LOCAL_STATEMENT_FIXTURE"}
    url = f"{root}/statement-fixtures"
    assert client.post(url, json=statement).status_code == 401
    data = client.post(url, headers=OWNER, json=statement)
    assert data.status_code == 201, data.text
    assert data.json()["budget_variance_minor"] == -15
    assert data.json()["actual_accessible_funds_minor"] is None
    assert client.post(url, headers=OWNER, json=statement).json() == data.json()
    assert client.post(url, headers=OWNER, json={**statement, "closing_minor": 421}).status_code == 422
    future = {**statement, "id": str(uuid4()), "start": today.isoformat(), "end": today.isoformat(),
              "opening_minor": 420, "closing_minor": 340, "entries": [{**row, "posted_on": today.isoformat()}]}
    assert client.post(url, headers=OWNER, json=future).status_code == 409
    assert client.post(url, headers=OWNER, json={**future, "purpose": "HOUSEHOLD"}).status_code == 409
    home = {**statement, "id": str(uuid4()), "account_ref": "household-a", "purpose": "HOUSEHOLD"}
    assert client.post(url, headers=OWNER, json=home).json()["protected_balance_minor"] == 420

    from app.models.completion_registry import KnowledgeRegistryItem, LearningFeedbackRecord

    for model in (KnowledgeRegistryItem, LearningFeedbackRecord):
        model.__table__.create(engine)
    evaluation = "/api/completion/phase3/universal-opportunity/evaluate"
    claim = {"basis": "LOCAL_STATEMENT_FIXTURE", "statement_id": statement["id"],
             "sha256": data.json()["sha256"], "closing_minor": 420}

    def challenge_claim(claim, **overrides):
        return client.post(evaluation, json={"shadow_mode": True, "persist_decision": False, "opportunities": [{
            "opportunity_id": "treasury-history", "engine_id": SCOPE["engine_id"], "legacy": SCOPE["legacy_instance_id"],
            "jurisdiction": SCOPE["jurisdiction"], "title": "Treasury history", "summary": "Preserve verified fixture scope.",
            "specialist_inputs": {"business_id": SCOPE["business_id"], "mimir_outcome_claims": [claim]},
            **overrides,
        }]})

    proof = challenge_claim(claim)
    assert proof.status_code == 200, proof.text
    assert proof.json()["evaluations"][0]["verified_mimir_claims"] == [
        {**claim, "actual_accessible_funds_minor": None, "evidence_scope": "LOCAL_STATEMENT_FIXTURE_ONLY"},
    ]
    assert challenge_claim({**claim, "closing_minor": 999}).status_code == 409
    assert challenge_claim(claim, jurisdiction="CA-ON").status_code == 409
    assert challenge_claim({**claim, "actual_accessible_funds_minor": 420}).status_code == 422

    post(client, "mandates", mandate(today))
    economic_row = post(client, "performance", performance(today, operating_receipts=94, operating_costs=55))
    economic_claim = {"basis": "ECONOMIC_PERFORMANCE_FIXTURE", "record_id": economic_row["id"],
                      "sha256": economic_row["sha256"], "period_net_minor": 39}
    assessment = challenge_claim(economic_claim)
    assert assessment.status_code == 200, assessment.text
    assert assessment.json()["evaluations"][0]["verified_mimir_claims"] == [{
        **economic_claim, "evidence_scope": "ECONOMIC_PERFORMANCE_FIXTURE_ONLY", "verified_real_world_outcome": False,
    }]
    assert challenge_claim({**economic_claim, "period_net_minor": 40}).status_code == 409
    assert challenge_claim(economic_claim, jurisdiction="CA-ON").status_code == 409
    assert challenge_claim({**economic_claim, "verified_real_world_outcome": True}).status_code == 422

    from app.loki.evidence import artifact_digest
    from app.pantheon.monitor import utc_now, verified_report

    from app.models.media_engine import MediaContent
    from app.models.prime_specialist_schedule import PrimeScheduleTrigger, PrimeSpecialistSchedule
    from app.routers.prime_specialist_schedules import run_due_schedule

    for model in (MediaContent, PrimeSpecialistSchedule, PrimeScheduleTrigger):
        model.__table__.create(engine)
    schedule_id = str(uuid4())
    schedule_root = "/api/prime/specialist-schedules"
    registered = client.post(schedule_root, headers=OWNER, json={
        "schedule_id": schedule_id, "business_id": SCOPE["business_id"],
        "cadence_seconds": 300, "duration_seconds": 1800,
        "opportunity": {"opportunity_id": "treasury-statement-review", "engine_id": SCOPE["engine_id"],
                        "legacy": SCOPE["legacy_instance_id"], "jurisdiction": SCOPE["jurisdiction"],
                        "title": "Treasury integrity rehearsal", "summary": "Observe scoped account evidence."},
    })
    assert registered.status_code == 201, registered.text

    assigned = client.post("/api/prime/pantheon/assignments", headers=OWNER, json={
        **SCOPE, "assignment_id": str(uuid4()), "role": "NJORD", "cadence_seconds": 120,
        "duration_seconds": 1800,
    })
    assert assigned.status_code == 201, assigned.text
    at = utc_now() + timedelta(seconds=1)
    with Session(engine) as db:
        result = run_assignment(db, "NJORD", now=at)
        report = verified_report(db, result["report_event_id"])
        economic = report["observations"]["economic_reassessment"]
        assert economic["verified_performance_claim"]["record_id"] == economic_claim["record_id"]
        contradictory = {**report, "observations": {
            **report["observations"], "economic_reassessment": {**economic, "period_net_minor": 40},
        }}
        reference = report["report_event_id"]
        challenge_result = challenge({"artifact_type": "pantheon_report", "reference": reference,
                                      "raw_input": contradictory,
                                      "artifact_sha256": artifact_digest("pantheon_report", reference, contradictory)})
        assert any(f.category == "economic_fixture_contradiction" and f.severity == "critical"
                   for f in challenge_result.findings)
        treasury = report["observations"]["treasury_statement_evidence"]
        assert treasury["actual_accessible_funds_minor"] is None
        [business] = treasury["accounts"]
        assert business["status"] == "MATCHED_FIXTURE"
        assert business["statement_id"] == statement["id"] and business["closing_minor"] == 420
        account = db.query(StatementAccount).filter_by(purpose="BUSINESS").one()
        last_head = account.head_id
        account.head_id = uuid4()
        db.commit()
        result = run_assignment(db, "NJORD", now=at + timedelta(seconds=120))
        report = verified_report(db, result["report_event_id"])
        assert report["observations"]["treasury_statement_evidence"]["accounts"][0]["status"] == "EVIDENCE_CONFLICT"
        challenge_ref = report["report_event_id"]
        review = challenge({"artifact_type": "pantheon_report", "reference": challenge_ref, "raw_input": report,
                            "artifact_sha256": artifact_digest("pantheon_report", challenge_ref, report)})
        assert any(f.category == "treasury_statement_conflict" and f.severity == "critical" for f in review.findings)
        assert run_due_schedule(db, now=at + timedelta(seconds=120))["status"] == "evaluated"
        prime = client.get(f"{schedule_root}/{schedule_id}").json()["latest_report"]
        assert prime["recommendation"]["heimdall_decision"] == "HOLD"
        reassessment = prime["operating_reassessment"]
        assert "TREASURY_STATEMENT_EVIDENCE_CONFLICT" in reassessment["blockers"]
        assert reassessment["treasury_statement_evidence"]["actual_accessible_funds_minor"] is None
        account.head_id = last_head
        db.commit()

    software = {"asset_ref": "fixture:licensable-software", "kind": "SOFTWARE",
                "rights": "REUSE_PERMITTED", "projected_liquidation_minor": 90, "obligations": []}
    approval, _ = queue_review(client, plan(action="EXIT", requested_additional_minor=0, assets=[software]), reconsider=True)
    decision = post(client, "decisions", approval)
    entry = {"external_ref": "recovery-example", "posted_on": today.isoformat(), "amount_minor": 61,
             "category": "ASSET_RECOVERY"}
    fixture = {**future, "closing_minor": 481, "entries": [entry]}
    response = client.post(url, headers=OWNER, json=fixture)
    assert response.status_code == 201, response.text
    recovery = {"id": str(uuid4()), "scope": SCOPE, "exit_decision_id": decision["id"],
                "asset_ref": software["asset_ref"], "statement_id": fixture["id"], "entry_ref": entry["external_ref"]}
    outcome = post(client, "asset-recovery-fixtures", recovery)
    assert outcome["projected_liquidation_minor"] == 90 and outcome["observed_statement_fixture_minor"] == 61
    assert outcome["actual_recovered_capital_minor"] is None
    post(client, "asset-recovery-fixtures", {**recovery, "id": str(uuid4())}, 409)
    with Session(engine) as db:
        assert db.query(VaultBalance).one().balance == 987
        assert db.query(RevenueLedger).count() == 0


@pytest.mark.parametrize("kind", ["SAAS", "SERVICE", "REAL_ESTATE"])
def test_venture_rehearsal_shares_stress_gates_and_rechecks_withdrawn_sources(economic_client, kind):
    from app.models.completion_registry import KnowledgeRegistryItem, LearningFeedbackRecord
    from app.models.foundry_evidence import FoundryEvidence
    from app.models.media_engine import MediaContent
    from app.models.prime_specialist_schedule import PrimeScheduleTrigger, PrimeSpecialistSchedule
    from app.pantheon.monitor import utc_now
    from app.routers.prime_specialist_schedules import run_due_schedule

    client, engine = economic_client
    for model in (FoundryEvidence, MediaContent, KnowledgeRegistryItem, LearningFeedbackRecord,
                  PrimeSpecialistSchedule, PrimeScheduleTrigger):
        model.__table__.create(engine)
    today = utc_now().date()
    post(client, "mandates", mandate(today, max_cumulative_loss=5000))
    post(client, "performance", performance(today))
    post(client, "liquidity", liquidity(today))
    root = "/api/prime/foundry"
    requests = {}
    for key, units in (("adverse-case", 8), ("viable-case", 14)):
        source = {
            **SCOPE, "evidence_id": str(uuid4()), "kind": kind, "evidence_class": "SIMULATION",
            "title": f"{kind} {key} internal evidence", "source_ref": f"fixture:{key}",
            "observed_on": today.isoformat(), "expires_on": (today + timedelta(days=2)).isoformat(),
            "currency": "CAD", "unit_price": 100, "variable_cost_per_unit": 25, "acquisition_cost_per_unit": 0,
            "monthly_fixed_cost": 500, "monthly_units": units, "startup_capital": 120, "test_cost": 10,
            "rights_attestation": "AUTHORIZED_INTERNAL_RESEARCH",
        }
        stored = client.post(f"{root}/evidence", headers=OWNER, json=source)
        assert stored.status_code == 201, stored.text
        requests[key] = source
        post(client, "opportunities", option(today, key, origin="FOUNDRY", foundry_evidence_id=source["evidence_id"]))
    report_ids = {}
    for role in ("NORNS", "LOKI"):
        response = client.post("/api/prime/pantheon/assignments", headers=OWNER, json={
            **SCOPE, "assignment_id": str(uuid4()), "role": role, "cadence_seconds": 300, "duration_seconds": 1800,
        })
        assert response.status_code == 201, response.text
        with Session(engine) as db:
            report_ids[role] = run_assignment(db, role)["report_event_id"]

    schedule_root = "/api/prime/specialist-schedules"
    schedules = {}
    for key, source in requests.items():
        candidate = client.get(f"{root}/reports/{report_ids['NORNS']}/candidate/{source['evidence_id']}")
        assert candidate.status_code == 200, candidate.text
        proposal = candidate.json()["proposal"]
        schedule_id = str(uuid4())
        prepared = client.post(schedule_root, headers=OWNER, json={
            "schedule_id": schedule_id, "business_id": SCOPE["business_id"], "opportunity": proposal,
            "cadence_seconds": 300, "duration_seconds": 1800,
            "on_economic_reassessment": key == "viable-case",
        })
        assert prepared.status_code == 201, prepared.text
        schedules[key] = schedule_id
    at = utc_now() + timedelta(seconds=1)
    with Session(engine) as db:
        assert [run_due_schedule(db, now=at)["status"] for _ in schedules] == ["evaluated", "evaluated"]
    adverse = client.get(f"{schedule_root}/{schedules['adverse-case']}").json()["latest_report"]
    viable = client.get(f"{schedule_root}/{schedules['viable-case']}").json()["latest_report"]
    assert adverse["recommendation"]["heimdall_decision"] == "HOLD"
    assert adverse["operating_reassessment"]["blockers"] == ["STRESSED_OPERATING_CONTRIBUTION_NEGATIVE"]
    assert viable["operating_reassessment"]["blockers"] == []
    assert viable["operating_reassessment"]["source_assessment"]["economics"]["verified_revenue_minor"] is None
    assessment = post(client, "assessment", SCOPE, 200)
    ranked = {item["opportunity_key"]: item for item in assessment["alternatives"]}
    assert ranked["adverse-case"]["foundry_economics"]["stress_monthly_operating_contribution_minor"] == -50
    assert "STRESSED_OPERATING_CONTRIBUTION_NEGATIVE" in ranked["adverse-case"]["blockers"]
    assert {"field": "projected_annual_net", "declared_minor": 1800, "used_minor": 1200} in ranked["adverse-case"]["projection_differences"]
    assert ranked["viable-case"]["foundry_economics"]["stress_monthly_operating_contribution_minor"] == 250
    assert assessment["best_eligible_alternative_key"] == "viable-case"

    denied, _ = queue_review(client, plan(action="REDEPLOY", alternative_key="adverse-case"), reconsider=False)
    denial = post(client, "decisions", denied, 409)
    assert "REDEPLOYMENT_ALTERNATIVE_UNJUSTIFIED" in denial["detail"]["blockers"]
    reviewed, _ = queue_review(client, plan(action="REDEPLOY", alternative_key="viable-case"), reconsider=True)
    accepted = post(client, "decisions", reviewed)
    assert accepted["reserved_simulation_minor"] == 120 and accepted["execution_authorized"] is False

    with Session(engine) as db:
        assert run_due_schedule(db, now=at)["status"] == "evaluated"  # Consume the reviewed reservation.
    viable_id = requests["viable-case"]["evidence_id"]
    for _ in range(2):
        assert client.delete(f"{root}/evidence/{viable_id}", headers=OWNER).status_code == 200
    assert client.get(f"{schedule_root}/{schedules['viable-case']}").json()["queued_economic_count"] == 1
    assert client.get(f"{schedule_root}/{schedules['adverse-case']}").json()["queued_economic_count"] == 0
    with Session(engine) as db:
        assert run_due_schedule(db, now=at)["status"] == "evaluated"
        assert run_due_schedule(db, now=at)["status"] == "idle"
        god_reports = [run_assignment(db, "NORNS", now=at) for _ in range(2)]
        assert [report["status"] for report in god_reports] == ["observed", "observed"]
        norns = [db.query(LegacyOrchestrationEvent).filter_by(event_id=report["report_event_id"]).one()
                 for report in god_reports]
        assert {json.loads(row.payload_json)["trigger"] for row in norns} == {
            "FOUNDRY_SOURCE_WITHDRAWN", "ECONOMIC_REASSESSMENT",
        }

    updated = client.get(f"{schedule_root}/{schedules['viable-case']}").json()["latest_report"]
    assert updated["trigger"] == "FOUNDRY_SOURCE_WITHDRAWN"
    assert updated["trigger_source_withdrawal_id"].startswith(f"WITHDRAWN-{viable_id}-")
    assert updated["scheduled_for"] is None
    assert updated["recommendation"]["heimdall_decision"] == "HOLD"
    assert "FOUNDRY_SOURCE_NO_LONGER_CURRENT" in updated["operating_reassessment"]["blockers"]
    assert post(client, "assessment", SCOPE, 200)["best_eligible_alternative_key"] is None
    with Session(engine) as db:
        assert db.query(RevenueLedger).count() == 0
        report_id = updated["report_event_id"]
        evidence = operating_evidence(db)
        alert = next(item for item in evidence["latest_prime_advisory_alerts"] if item["report_event_id"] == report_id)
        assert alert["trigger"] == "FOUNDRY_SOURCE_WITHDRAWN"
        assert alert["blockers"] == ["FOUNDRY_SOURCE_NO_LONGER_CURRENT"]
        assert alert["execution_authorized"] is False
        attention = owner_attention(db)
        assert attention["delivery_attempted"] is False
        assert f"prime_advisory:{report_id}" in {entry["notification_id"] for entry in attention["entries"]}
        receipt = db.query(LegacyOrchestrationEvent).filter_by(event_id=report_id).one()
        payload = json.loads(receipt.payload_json)
        payload.pop("report_sha256")
        receipt.payload_json = json.dumps(payload)
        db.commit()
        attention = {entry["notification_id"] for entry in owner_attention(db)["entries"]}
        assert f"prime_advisory:{report_id}" not in attention
        assert f"prime_integrity:{report_id}" in attention



def test_prime_reassesses_queued_economic_evidence_without_waiting_for_cadence(economic_client, monkeypatch):
    from app.models.completion_registry import KnowledgeRegistryItem, LearningFeedbackRecord
    from app.models.media_engine import MediaContent
    from app.models.prime_specialist_schedule import PrimeScheduleTrigger, PrimeSpecialistSchedule
    from app.routers.prime_specialist_schedules import _utc_now, run_due_schedule
    from app.services.economic_control import trigger_reassessment

    client, engine = economic_client
    for model in (MediaContent, KnowledgeRegistryItem, LearningFeedbackRecord,
                  PrimeSpecialistSchedule, PrimeScheduleTrigger):
        model.__table__.create(engine)
    now = _utc_now()
    today = now.date()
    post(client, "mandates", mandate(today))
    post(client, "performance", performance(today - timedelta(days=1)))
    post(client, "liquidity", liquidity(today))
    root = "/api/prime/specialist-schedules"

    def schedule(scope, *, economic):
        schedule_id = str(uuid4())
        response = client.post(root, headers=OWNER, json={
            "schedule_id": schedule_id, "business_id": scope["business_id"],
            "cadence_seconds": 300, "duration_seconds": 1800,
            "on_economic_reassessment": economic, "on_verified_outcome": not economic,
            "opportunity": {
                "opportunity_id": "prime-economic-rehearsal", "engine_id": scope["engine_id"],
                "legacy": scope["legacy_instance_id"], "jurisdiction": scope["jurisdiction"],
                "title": "Economic trigger rehearsal", "summary": "Internal simulation and fixture evidence.",
            },
        })
        assert response.status_code == 201, response.text
        return f"{root}/{schedule_id}", response.json()

    scoped, _ = schedule(SCOPE, economic=True)
    outcome_only, _ = schedule(SCOPE, economic=False)
    mirror, _ = schedule(MIRROR, economic=True)
    at = now + timedelta(seconds=3)
    with Session(engine) as db:
        assert [run_due_schedule(db, now=at)["status"] for _ in range(3)] == ["evaluated"] * 3
    before = client.get(scoped).json()
    assert before["latest_report"]["operating_reassessment"]["economic_reassessment"]["period_net_minor"] == 50

    loss = performance(today, operating_receipts=20, operating_costs=170)
    receipt = post(client, "performance", loss)
    assert post(client, "performance", loss) == receipt
    containment = {"id": str(uuid4()), "scope": SCOPE,
                   "rationale": "Pause this fixture after the cumulative loss breach."}
    post(client, "containment", containment)
    assert client.get(scoped).json()["queued_economic_count"] == 2
    assert client.get(outcome_only).json()["queued_economic_count"] == 0
    assert client.get(mirror).json()["queued_economic_count"] == 0
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    with Session(engine) as db:
        assert run_due_schedule(db, now=at) == {"status": "blocked", "emergency_stop": True}
    assert client.get(scoped).json()["queued_economic_count"] == 2
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    with Session(engine) as db:
        assert [run_due_schedule(db, now=at)["status"] for _ in range(2)] == ["evaluated"] * 2
        assert run_due_schedule(db, now=at) == {"status": "idle"}
        trigger_reassessment(db, SCOPE, UUID(loss["id"]), now)
        db.commit()
        assert run_due_schedule(db, now=at)["status"] == "replayed"
        trigger_reassessment(db, SCOPE, uuid4(), now)
        db.commit()
        assert run_due_schedule(db, now=at)["status"] == "blocked"
        assert db.query(RevenueLedger).count() == 0

    blocked = client.get(scoped).json()
    assert blocked["next_due_at"] == before["next_due_at"]
    assert blocked["latest_report"]["reason"] == "Economic trigger evidence failed revalidation"
    assert blocked["latest_report"]["trigger"] == "ECONOMIC_REASSESSMENT"
    with Session(engine) as db:
        rows = db.query(LegacyOrchestrationEvent).filter_by(event_type="PRIME_SPECIALIST_SHADOW_REPORT").all()
    reports = [json.loads(row.payload_json) for row in rows]
    loss_report = next(report for report in reports if report.get("trigger_economic_event_id") == f"ECON-{loss['id']}")
    assert loss_report["trigger_outcome_event_id"] is None
    assert loss_report["effect"] == "ADVISORY_ONLY"
    assert loss_report["recommendation"]["heimdall_decision"] == "HOLD"
    assert loss_report["operating_reassessment"]["economic_reassessment"]["cumulative_loss_minor"] == 150

def test_legacy_failover_pauses_contained_scope_before_reassignment(economic_client):
    client, engine = economic_client
    post(client, "mandates", mandate(datetime.now(timezone.utc).date()))
    post(client, "containment", {"id": str(uuid4()), "scope": SCOPE,
                                  "rationale": "Pause economic work before legacy failover."})
    with Session(engine) as db:
        for legacy in db.query(LegacyInstanceRegistryItem):
            legacy.assigned_businesses_json = '["venture-local","unrelated-unit","restricted-destination"]'
            if legacy.legacy_instance_id == MIRROR["legacy_instance_id"]:
                legacy.local_knowledge_context_json = json.dumps({
                    **MIRROR, "business_id": "restricted-destination", "data_namespace": "recovery-namespace",
                })
                legacy.assigned_jurisdictions_json = '["CA-MB","CA-ON"]'
        for action, business in (("held-failover", SCOPE["business_id"]), ("healthy-failover", "unrelated-unit"),
                                 ("held-at-destination", "restricted-destination"),
                                 ("wrong-jurisdiction", "unrelated-unit"), ("bfd_pinned-fixture", "unrelated-unit")):
            db.add(LegacyInstanceWorkItem(
                action_id=action, idempotency_key=action, legacy_instance_id=SCOPE["legacy_instance_id"],
                business_id=business, engine_id=SCOPE["engine_id"],
                jurisdiction="US-TX" if action == "wrong-jurisdiction" else SCOPE["jurisdiction"],
                status="queued", industry="fixture", objective="Internal reassignment", namespace="disposable",
                payload_json="{}",
            ))
        db.commit()
    destination = {**MIRROR, "business_id": "restricted-destination"}
    post(client, "mandates", mandate(datetime.now(timezone.utc).date(), scope=destination))
    post(client, "containment", {"id": str(uuid4()), "scope": destination,
                                  "rationale": "Hold the affected receiving business."})
    denied = client.post("/api/completion/legacy-orchestration/work/assign", json={
        **SCOPE, "action_id": "new-held-legacy", "idempotency_key": "new-held-legacy",
        "industry": "fixture", "objective": "Attempt fresh assignment during containment",
        "data_namespace": "disposable",
    })
    assert denied.status_code == 409 and "containment" in denied.json()["detail"]
    result = client.post("/api/completion/legacy-orchestration/failover", json={
        "failed_instance_id": SCOPE["legacy_instance_id"], "recovery_instance_id": MIRROR["legacy_instance_id"],
    })
    assert result.status_code == 200, result.text
    assert result.json()["containment_paused"] == 2
    assert result.json()["scope_paused"] == 2
    assert result.json()["reassigned"] == 1
    with Session(engine) as db:
        assert db.query(LegacyInstanceWorkItem).filter_by(action_id="new-held-legacy").count() == 0
        held = db.query(LegacyInstanceWorkItem).filter_by(action_id="held-failover").one()
        healthy = db.query(LegacyInstanceWorkItem).filter_by(action_id="healthy-failover").one()
        assert (held.status, held.legacy_instance_id) == ("paused", SCOPE["legacy_instance_id"])
        assert (healthy.status, healthy.legacy_instance_id, healthy.namespace) == (
            "queued", MIRROR["legacy_instance_id"], "recovery-namespace",
        )
        for paused_id in ("wrong-jurisdiction", "bfd_pinned-fixture"):
            paused = db.query(LegacyInstanceWorkItem).filter_by(action_id=paused_id).one()
            assert (paused.status, paused.legacy_instance_id) == ("paused", SCOPE["legacy_instance_id"])
        held_at_destination = db.query(LegacyInstanceWorkItem).filter_by(action_id="held-at-destination").one()
        assert (held_at_destination.status, held_at_destination.legacy_instance_id) == ("paused", SCOPE["legacy_instance_id"])


def test_business_hold_blocks_alternate_currency_reservation_and_dispatch(economic_client):
    client, engine = economic_client
    today = datetime.now(timezone.utc).date()
    post(client, "mandates", mandate(today))
    post(client, "mandates", mandate(today, scope=MIRROR, currency="USD"))
    post(client, "performance", performance(today, scope=MIRROR))
    post(client, "liquidity", liquidity(today, scope=MIRROR))
    pre_hold, _ = queue_review(client, plan(scope=MIRROR), reconsider=True)

    post(client, "containment", {"id": str(uuid4()), "scope": SCOPE,
                                 "rationale": "Freeze this business while operator evidence is reviewed."})
    post(client, "decisions", pre_hold, 409)
    preview = post(client, "review-artifact", pre_hold["plan"], 200)["raw_input"]["analysis"]
    assert "RELATED_BUSINESS_CONTAINED" in preview["blockers"]
    assert preview["new_exposure_available_minor"] == 0
    reviewed, _ = queue_review(client, plan(scope=MIRROR), reconsider=False)
    refused = post(client, "decisions", reviewed, 409)
    assert "RELATED_BUSINESS_CONTAINED" in refused["detail"]["blockers"]

    new_scope = {**SCOPE, "legacy_instance_id": "alternate-registered-root"}
    with Session(engine) as db:
        db.add(LegacyInstanceRegistryItem(
            legacy_instance_id=new_scope["legacy_instance_id"], display_name="Alternate root fixture",
            status="PASS", synchronization_status="SYNCED", engines_json='["candidate-engine"]',
            assigned_businesses_json='["venture-local"]', assigned_jurisdictions_json='["CA-MB"]',
            local_knowledge_context_json=json.dumps(new_scope),
        ))
        db.commit()
    rejected = post(client, "mandates", mandate(today, scope=new_scope, opening_additional_funding=1,
                                               opening_receipt_ref="fixture:alternate-opening"), 409)
    assert "containment" in rejected["detail"]
    post(client, "mandates", mandate(today, scope=new_scope))
    with Session(engine) as db:
        with pytest.raises(HTTPException, match="containment"):
            require_no_containment(db, new_scope)
        assert all(row.committed_minor == 0 for row in db.query(EconomicPool))
    # Preserve loss and liability evidence collection while blocking new exposure.
    post(client, "obligations", {"id": str(uuid4()), "scope": MIRROR, "obligation_key": "held-invoice",
                                 "due_on": today.isoformat(), "status": "OPEN", "amount_minor": 3,
                                 "evidence_ref": "fixture:held-invoice"})


def test_personal_allocation_binds_closed_month_cash_and_protects_obligations(economic_client, monkeypatch):
    from app.models.treasury_reconciliation import StatementAccount, StatementEntry, StatementImport
    from app.routers import floor_control, foundry_checkout

    client, engine = economic_client
    for model in (StatementAccount, StatementEntry, StatementImport):
        model.__table__.create(engine)
    clock = datetime(2026, 11, 2, tzinfo=timezone.utc)

    class FixtureDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return clock if tz is not None else clock.replace(tzinfo=None)

    monkeypatch.setattr(floor_control, "datetime", FixtureDateTime)
    monkeypatch.setattr(economic_control, "now", lambda: clock)
    today = clock.date()
    post(client, "mandates", mandate(today, min_operating_reserve=300000))
    post(client, "liquidity", liquidity(today, unrestricted_pool_minor=3_000_000))
    start, end = "2026-10-01", "2026-10-31"
    statement_id, order_id = str(uuid4()), str(uuid4())
    statement = {"id": statement_id, "scope": SCOPE, "source_id": "fixture:monthly",
                 "account_ref": "business-current", "purpose": "BUSINESS", "currency": "CAD",
                 "start": start, "end": end, "opening_minor": 1_800_000, "closing_minor": 3_000_000,
                 "outstanding_liabilities_minor": 100000, "expense_budget_minor": 0,
                 "entries": [{"external_ref": "capture", "posted_on": end, "category": "TRANSFER",
                              "amount_minor": 1_200_000}], "basis": "LOCAL_STATEMENT_FIXTURE"}
    response = client.post("/api/governance/floor/treasury/statement-fixtures", headers=OWNER, json=statement)
    assert response.status_code == 201, response.text
    checkout = {"order_id": order_id, "net_minor": 1_200_000, "fixture_cost_minor": 50000,
                "currency": "CAD", "sha256": "a" * 64, "settlements": [{"posted_on": end, "statement_id": statement_id}]}
    monkeypatch.setattr(foundry_checkout, "closed_checkout_proof", lambda *args, **kwargs: checkout)
    post(client, "performance", performance(
        today, start=start, end=end, operating_receipts=1_200_000, operating_costs=50000,
        receipt_ref=f"checkout-fixture:{order_id}", checkout_order_id=order_id, checkout_sha256=checkout["sha256"],
    ))
    request = {"scope": SCOPE, "statement_id": statement_id, "essential_household_minor": 350000,
               "personal_reserve_target_minor": 100000, "personal_reserve_balance_minor": 0,
               "operating_reserve_minor": 200000, "corporate_tax_reserve_minor": 150000}
    path = "/api/governance/floor/wealth/personal-allocation-receipts"
    assert client.post(path, json=request).status_code == 401
    issued = client.post(path, headers=OWNER, json=request)
    assert issued.status_code == 201, issued.text
    result = issued.json()
    assert result["recommended_personal_minor"] == 400000
    assert result["business_protections_minor"] == 550020
    assert result["personal_breakdown"] == {"essentials_minor":350000, "reserve_minor":50000, "remaining_personal_minor":0}
    assert result["actual_accessible_funds_minor"] is None and not result["funds_movement_authorized"]
    assert client.post(path, headers=OWNER, json=request).json() == result
    review = client.post(path.replace("receipts", "review-artifact"), headers=OWNER, json=request).json()
    review_input = {"artifact_type": review["artifact_type"], "reference": review["heimdall_reference_id"],
                    "raw_input": review["raw_input"], "artifact_sha256": review["artifact_sha256"]}
    assert {finding.category for finding in challenge(review_input).findings} == {"allocation_review_required"}
    from app.loki.evidence import artifact_digest

    modified = {**review_input["raw_input"], "funds_movement_authorized": True, "recommended_personal_minor": 1100000}
    review_input["raw_input"] = modified
    review_input["artifact_sha256"] = artifact_digest("personal_allocation", review_input["reference"], modified)
    assert {"allocation_authority_conflict", "allocation_capital_conflict"} <= {
        finding.category for finding in challenge(review_input).findings if finding.severity == "critical"
    }
    held = client.post(path, headers=OWNER, json={**request, "additional_obligations_minor":3_000_000}).json()
    assert held["recommended_personal_minor"] == 0 and held["contingency_review_recommended"]
    from app.models.foundry_evidence import FoundryEvidence
    from app.services.commercial_targets import CommercialTargetsIn, review_commercial_targets
    from app.services.foundry_discovery import EvidenceIn
    from app.services.specialist_triggers import outcome_scope_key

    FoundryEvidence.__table__.create(engine)
    evidence = EvidenceIn(evidence_id=uuid4(), **SCOPE, kind="SERVICE", evidence_class="SIMULATION",
                          title="Operating scenario fixture", source_ref="fixture:service-unit-cost",
                          observed_on=today, expires_on=today, currency="CAD", unit_price=100000,
                          variable_cost_per_unit=20000, acquisition_cost_per_unit=10000, monthly_fixed_cost=50000,
                          startup_capital=200000, test_cost=10000, monthly_units=100,
                          rights_attestation="AUTHORIZED_INTERNAL_RESEARCH")
    params = {"allocation": request, "net_personal_target_minor": 320000, "estimated_personal_tax_bp": 2000,
              "reserve_addition_minor": 20000, "candidates": [{
                  "evidence_id": str(evidence.evidence_id), "in_month_settlement_bp": 8000,
                  "fulfillment_limit_units": 23, "units_per_customer": 2, "experiment_budget_minor": 5000,
              }]}
    endpoint = "/api/weweb/owner-startup/commercial-targets"
    unauthorized = client.post(endpoint, headers=OWNER, json=params)
    assert unauthorized.status_code == 401 and unauthorized.headers["cache-control"] == "no-store"
    body = evidence.model_dump(mode="json")
    with Session(engine) as db:
        row = FoundryEvidence(id=evidence.evidence_id, scope_key=outcome_scope_key(SCOPE),
                              source_ref=evidence.source_ref, observed_on=today, expires_on=today, payload=body,
                              digest=artifact_digest("foundry_evidence", str(evidence.evidence_id), body))
        db.add(row)
        db.commit()
        scenario = CommercialTargetsIn.model_validate(params)
        projection = review_commercial_targets(db, scenario, today)
        assert projection["baseline_allocation_sha256"] == result["sha256"]
        assert projection["required_gross_personal_minor"] == 400000
        assert projection["required_distributable_profit_minor"] == 1000000
        assert projection["fixture_distributable_gap_minor"] == 0
        option = projection["options"][0]
        assert option["required_units"] == 25 and option["required_customers"] == 13
        assert option["required_booked_sales_minor"] == 2500000
        assert option["estimated_in_month_cash_minor"] == 2000000
        assert option["required_acquisition_budget_minor"] == 250000
        assert option["blockers"] == ["POSITIVE_SOURCED_DEMAND_SAMPLE_MISSING", "TEST_COST_EXCEEDS_SCENARIO_BUDGET",
                                      "VOLUME_EXCEEDS_DECLARED_DEMAND_OR_FULFILLMENT"]
        assert projection["verified_after_tax_income_minor"] is None
        assert projection["requires_independent_review"] and not projection["external_action_authorized"]

        from app.services.startup_independence import StartupIndependenceIn, review_startup_independence

        independence = StartupIndependenceIn(
            registration_date=date(2026, 10, 1), registration_evidence_ref="fixture:registration",
            reporting_month=date(2026, 10, 1), reconciled_allocation=request,
            monthly_essentials_minor=350000, reserve_months=3, reserve_balance_minor=0,
            monthly_stretch_low_minor=800000, monthly_stretch_high_minor=1200000,
            opening_unrestricted_cash_fixture_minor=0, establishment_minor=1000,
            operating_minor=0, business_reserve_minor=0, experiment_minor=0,
        )
        independence_review = review_startup_independence(db, independence, today)
        linked = independence_review["reconciled_monthly_fixture"]
        assert linked["allocation_sha256"] == result["sha256"]
        assert linked["economic_performance"]["checkout_sha256"] == checkout["sha256"]
        assert linked["recommendation_gross_personal_minor"] == result["recommended_personal_minor"]
        assert independence_review["capital_scenarios"][0]["total_plan_gap_minor"] == 1000
        assert independence_review["verified_available_cash_minor"] is None
        assert independence_review["verified_after_tax_income_minor"] is None
        with pytest.raises(HTTPException, match="private review month"):
            review_startup_independence(db, independence.model_copy(update={"reporting_month": today.replace(day=1)}),
                                        today)

        low_settlement = CommercialTargetsIn.model_validate({
            **params, "candidates": [{**params["candidates"][0], "in_month_settlement_bp": 2000}],
        })
        blocked = review_commercial_targets(db, low_settlement, today)["options"][0]
        assert blocked["required_units"] is None
        assert "NONPOSITIVE_UNIT_MARGIN_OR_IN_MONTH_CASH" in blocked["blockers"]
        row.revoked = True
        db.commit()
        with pytest.raises(HTTPException, match="stale, revised or outside scope"):
            review_commercial_targets(db, scenario, today)
    checkout["sha256"] = "b" * 64
    assert client.post(path, headers=OWNER, json=request).status_code == 409


def test_scoped_bank_correction_blocks_new_exposure_and_prompts_independent_review(economic_client, monkeypatch):
    from app.loki.evidence import artifact_digest
    from app.services import stripe_bank_booking
    from app.services.economic_control import specialist_economics

    client, engine = economic_client
    today = datetime.now(timezone.utc).date()
    post(client, "mandates", mandate(today))
    post(client, "performance", performance(today))
    post(client, "liquidity", liquidity(today))
    assert post(client, "assessment", SCOPE, 200)["new_exposure_available_minor"] > 0
    correction = "STRIPE_BANK_CORRECTION_REQUIRED"
    monkeypatch.setattr(stripe_bank_booking, "scoped_bank_blockers",
                        lambda _db, scope, *, live: {correction} if scope == SCOPE else set())
    held = post(client, "assessment", SCOPE, 200)
    assert correction in held["blockers"] and held["suggested_action"] == "SUSPEND"
    assert held["new_exposure_available_minor"] == held["comparison_budget_minor"] == 0
    with Session(engine) as db:
        result = specialist_economics(db, "NJORD", SCOPE, today)
    assert correction in result["economic_reassessment"]["blockers"]
    reference = "bank-correction-test"
    report = {"scope": SCOPE, "role": "NJORD", "status": "observed", "observations": result,
              "verified_real_world_outcome": False, "external_authority": False}
    review = challenge({"artifact_type": "pantheon_report", "reference": reference, "raw_input": report,
                        "artifact_sha256": artifact_digest("pantheon_report", reference, report)})
    assert any(f.category == "bank_batch_correction_required" and f.severity == "critical" for f in review.findings)


def test_autonomous_customer_research_fixture(economic_client, loopback_api, monkeypatch):
    from pathlib import Path
    import runpy
    from app.models.go_live_state import GoLiveState

    client, engine = economic_client
    root = "/api/prime/customer-research/rehearsal"
    round_id = str(uuid4())
    token = str(uuid4())
    with Session(engine) as db:
        db.get(GoLiveState, 1).kill_switch_engaged = False
        db.commit()
    start = {"scope": SCOPE, "round_id": round_id, "topic": "fleet_records", "duration_hours": 24, "max_enrollments": 2,
             "reference_price_minor": 19900}
    scope = {"scope": SCOPE}
    participant = {**scope, "token": token}
    latest = f"{root}/{round_id}"

    def call(path, body, code=200, headers=None):
        response = client.post(path, json=body, headers=headers)
        assert response.status_code == code, response.text
        if code == 200:
            assert response.headers["cache-control"] == "no-store"
        return response.json()

    monkeypatch.setenv("VALHALLA_CUSTOMER_RESEARCH_REHEARSAL", "0")
    call(f"{root}/rounds", start, 503, OWNER)
    monkeypatch.setenv("VALHALLA_CUSTOMER_RESEARCH_REHEARSAL", "1")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENV", "test")
    call(f"{root}/rounds", start, 401)
    call(f"{root}/rounds", start, headers=OWNER)
    cron = Path(__file__).resolve().parents[1] / "tools" / "cron"
    monkeypatch.syspath_prepend(str(cron))
    advance = runpy.run_path(str(cron / "customer_research_worker.py"))["tick"]
    assert advance(loopback_api, round_id, SCOPE) == {"status": "invitation_prepared", "sent": False}
    assert call(f"{latest}/advance", scope)["status"] == "WAITING_FOR_VOLUNTARY_ANSWERS"
    call(f"{latest}/invitation", {"scope": MIRROR}, 404)
    enrollment = {**participant, "notice_version": "heimdall-structured-research-v1", "consent": True}
    call(f"{latest}/enroll", {**enrollment, "consent": False}, 422)
    call(f"{latest}/answer", {**participant, "step": "problem", "answer": "yes"}, 409)
    assert call(f"{latest}/enroll", enrollment)["step"] == "problem"
    call(f"{latest}/answer", {**participant, "step": "interest", "answer": "yes"}, 409)
    for step, value, following in (("problem", "yes", "authority"), ("authority", "yes", "effort"),
                                   ("effort", "1_to_4h", "interest"), ("interest", "yes", None)):
        command = {**participant, "step": step, "answer": value}
        reply = call(f"{latest}/answer", command)
        assert reply.get("step") == following
        assert call(f"{latest}/answer", command) == reply

    second = {**enrollment, "token": str(uuid4())}
    assert call(f"{latest}/enroll", second)["step"] == "problem"
    assert call(f"{latest}/answer", {**participant, "token": second["token"], "step": "problem",
                                     "answer": "no"})["status"] == "COMPLETED"
    call(f"{latest}/enroll", {**enrollment, "token": str(uuid4())}, 409)
    call(f"{latest}/decision", scope, 409)

    queued = advance(loopback_api, round_id, SCOPE)
    assert queued["status"] == "independent_review_queued"
    review = call(f"{latest}/review", scope)
    assert queued["artifact_sha256"] == review["artifact_sha256"]
    assert review == call(f"{latest}/review", scope)
    assert review["evidence"]["completed"] == 2
    assert review["evidence"]["stated_interest"] == 1
    assert review["evidence"]["verified_cac_minor"] is None
    assert token not in json.dumps(review)
    call(f"{latest}/decision", scope, 409)
    assert call(f"{latest}/advance", scope)["status"] == "WAITING_FOR_INDEPENDENT_REVIEW"

    worker = runpy.run_path(str(cron / "loki_analyst_worker.py"))["tick"]
    prime_headers = dict(loopback_api.headers)
    loopback_api.headers.clear()
    loopback_api.headers.update(REVIEWER)
    receipt = worker(loopback_api, "customer_research", "economic-independent-fixture")
    assert receipt["verified"] and receipt["review_id"] == review["review_id"]
    loopback_api.headers.clear()
    loopback_api.headers.update(prime_headers)

    for role in ("FREYJA", "NORNS", "NJORD", "TYR", "MIMIR"):
        enrolled = client.post("/api/prime/pantheon/assignments", headers=OWNER, json={
            **SCOPE, "assignment_id": str(uuid4()), "role": role, "cadence_seconds": 300, "duration_seconds": 1800,
        })
        assert enrolled.status_code == 201, enrolled.text
        with Session(engine) as db:
            report_id = run_assignment(db, role)["report_event_id"]
        report = client.get(f"/api/prime/pantheon/reports/{report_id}").json()
        observed = report["observations"]["customer_research"]
        assert observed["study_sha256"] == review["evidence"]["study_sha256"]
        assert "answers" not in observed

    assert advance(loopback_api, round_id, SCOPE)["status"] == "abstained"
    decision = call(f"{latest}/advance", scope)
    assert decision == call(f"{latest}/decision", scope)
    assert decision["decision"] == "ABSTAIN_PENDING_GENUINE_EVIDENCE"
    assert decision["external_action_authorized"] is False
    assert any("bias" in blocker for blocker in decision["blockers"])

    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    call(f"{latest}/invitation", scope, 503)
    assert call(f"{latest}/withdraw", participant)["answers_removed"]
    assert call(f"{latest}/withdraw", participant)["suppressed"]
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    call(f"{latest}/decision", scope, 409)
    call(f"{latest}/enroll", enrollment, 409)
    second_round = str(uuid4())
    call(f"{root}/rounds", {**start, "round_id": second_round}, headers=OWNER)
    call(f"{root}/{second_round}/invitation", scope)
    call(f"{root}/{second_round}/enroll", enrollment, 409)
    updated = call(f"{latest}/review", scope)
    assert updated["evidence"]["stated_interest"] == 0 and updated["evidence"]["withdrawn"] == 1
    assert updated["artifact_sha256"] != review["artifact_sha256"]
    from app.loki.evidence import artifact_digest

    overclaim = {**updated["evidence"], "paid_outcomes_verified": True, "stated_interest": 99,
                 "verified_cac_minor": 0}
    rejected = challenge({"artifact_type": "customer_research", "reference": round_id,
                          "raw_input": overclaim, "artifact_sha256": artifact_digest(
                              "customer_research", round_id, overclaim)})
    assert any(finding.category == "research_evidence_overreach" and finding.severity == "critical"
               for finding in rejected.findings)
    print("RESEARCH_REHEARSAL " + json.dumps({"initial_review": receipt, "decision": decision,
                                             "withdrawal_recheck": updated["artifact_sha256"]}))


@pytest.mark.parametrize("deal_client", ["disk"], indirect=True)
def test_authenticated_research_participant_browser_and_retention(economic_client, disposable_http_server, monkeypatch):
    import os
    from pathlib import Path
    import runpy
    import subprocess

    from starlette.applications import Starlette
    from starlette.routing import Mount
    from starlette.staticfiles import StaticFiles
    from app.models.auth_revocations import RevokedAccessToken
    from app.routers.auth_weweb import _auth_runtime
    from app.services import customer_research
    from app.users.models import AccountSettings, UserProfile

    client, engine = economic_client
    for model in (UserProfile, AccountSettings, RevokedAccessToken):
        model.__table__.create(engine, checkfirst=True)
    for key, value in {
        "APP_ENV": "test", "ENV": "test", "VALHALLA_CUSTOMER_RESEARCH_REHEARSAL": "1",
        "VALHALLA_RESEARCH_IDENTITY_HMAC": "local-fixture-identity-pseudonymization-only",
    }.items():
        monkeypatch.setenv(key, value)
    password = "disposable-research-account"
    ids = {}
    emails = {key: f"research-{key}@example.invalid" for key in ("participant", "browser", "outsider")}
    with Session(engine) as db:
        for key, email in emails.items():
            profile = UserProfile(first_name="Synthetic", last_name="Research", email=email)
            db.add(profile)
            db.flush()
            ids[key] = profile.user_id
            db.add(AccountSettings(user_id=profile.user_id, email_verified=True, account_locked=False,
                                   password_hash=_auth_runtime().pbkdf2_hash_password(password)))
        db.commit()

    round_id = str(uuid4())
    prime = "/api/prime/customer-research/rehearsal"
    root = f"/api/weweb/customer-research/{round_id}"
    data = {"scope": SCOPE, "round_id": round_id, "topic": "fleet_records", "duration_hours": 1,
            "max_enrollments": 2, "reference_price_minor": 19900, "identity_bound": True}
    scope = {"scope": SCOPE}
    opened = client.post(f"{prime}/rounds", json=data, headers=OWNER)
    assert opened.status_code == 200, opened.text
    assert client.post(f"{prime}/{round_id}/advance", json=scope).json()["sent"] is False
    for user in ("participant", "browser"):
        assert client.post(f"{root}/grant", json={**scope, "user_id": ids[user]}, headers=OWNER).status_code == 200
    assert client.post(f"{root}/grant", json={**scope, "user_id": ids["outsider"]}, headers=OWNER).status_code == 409

    def login(which):
        res = client.post("/api/weweb/login", json={"email": emails[which], "password": password})
        assert res.status_code == 200, res.text
        return {"Authorization": "Bearer " + res.json()["access_token"]}

    headers = login("participant")
    outsider = login("outsider")
    assert client.get(root).status_code == 401
    assert client.get(root, headers=outsider).status_code == 404
    assert client.post(root + "/grant", json={**scope, "user_id": ids["outsider"]},
                       headers={**outsider, "X-Prime-Control-Key": ""}).status_code == 401
    disclosure = client.get(root, headers=headers)
    assert disclosure.headers["cache-control"] == "no-store"
    notice = disclosure.json()
    assert notice["status"] == "CONSENT_REQUIRED"
    consent = {"consent": True, "notice_version": notice["notice"]["version"], "notice_sha256": notice["notice_sha256"]}
    assert client.post(root + "/enroll", headers=headers, json={**consent, "consent": False}).status_code == 422
    assert client.post(root + "/enroll", headers=headers, json={**consent, "notice_sha256": "0" * 64}).status_code == 422
    assert client.post(root + "/enroll", headers=headers, json={**consent, "user_id": ids["outsider"]}).status_code == 422
    assert client.post(f"{prime}/{round_id}/enroll", json={**scope, "token": str(uuid4()), "consent": True,
                       "notice_version": customer_research.NOTICE}).status_code == 409
    assert client.post(root + "/answer", headers=headers, json={"step": "problem", "answer": "yes"}).status_code == 409
    assert client.post(root + "/enroll", headers=headers, json=consent).json()["step"] == "problem"
    assert client.post(root + "/enroll", headers=headers, json=consent).json()["step"] == "problem"
    assert client.post(root + "/answer", headers=headers, json={"step": "interest", "answer": "yes"}).status_code == 409
    assert client.post(root + "/answer", headers=headers, json={"step": "problem", "answer": "yes"}).json()["step"] == "authority"

    # Reopen the disposable database through a new connection and loopback server.
    engine.dispose()
    with disposable_http_server(client) as network:
        assert network.get(root, headers=headers).json()["step"] == "authority"
        assert network.post(root + "/answer", headers=headers, json={"step": "authority", "answer": "no"}).json()["status"] == "COMPLETED"
        cron = Path(__file__).resolve().parents[1] / "tools" / "cron"
        monkeypatch.syspath_prepend(str(cron))
        loki = runpy.run_path(str(cron / "loki_analyst_worker.py"))["tick"]
        queued = client.post(f"{prime}/{round_id}/advance", json=scope).json()
        network.headers.clear()
        network.headers.update(REVIEWER)
        receipt = loki(network, "customer_research", "economic-independent-fixture")
        assert receipt["verified"] and receipt["artifact_sha256"] == queued["artifact_sha256"]
    assert client.post(f"{prime}/{round_id}/advance", json=scope).json()["decision"] == "ABSTAIN_PENDING_GENUINE_EVIDENCE"

    if os.environ.get("VALHALLA_BROWSER_ACCEPTANCE") == "1":
        repo = Path(__file__).resolve().parents[3]
        static = repo / "tests" / "browser-acceptance"
        app = Starlette(routes=[
            Mount("/__acceptance", app=StaticFiles(directory=static, html=True)),
            Mount("/__widgets", app=StaticFiles(directory=repo / "web" / "weweb-widgets")),
            Mount("/", app=client.app),
        ])
        with disposable_http_server(client, app=app) as network:
            result = subprocess.run(["node", str(static / "research.cjs")], text=True, capture_output=True,
                timeout=60, input=json.dumps({"origin": str(network.base_url), "round": round_id,
                                             "email": emails["browser"], "password": password}))
        assert result.returncode == 0, result.stderr
        print("\nRESEARCH_BROWSER " + result.stdout.strip())

    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    assert client.get(root, headers=headers).json()["status"] == "PAUSED"
    assert client.post(root + "/answer", headers=headers, json={"step": "authority", "answer": "no"}).status_code == 503
    assert client.post(root + "/withdraw", headers=headers).json()["answers_removed"]
    assert client.get(root, headers=headers).json()["status"] == "WITHDRAWN"
    assert client.post("/api/weweb/logout", headers=headers).status_code == 200
    assert client.get(root, headers=headers).status_code == 401
    headers = login("participant")
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    assert client.post(root + "/enroll", headers=headers, json=consent).status_code == 409
    assert client.post(f"{prime}/{round_id}/decision", json=scope).status_code == 409

    new_round = str(uuid4())
    assert client.post(f"{prime}/rounds", json={**data, "round_id": new_round}, headers=OWNER).status_code == 200
    assert client.post(f"/api/weweb/customer-research/{new_round}/grant",
                       json={**scope, "user_id": ids["participant"]}, headers=OWNER).status_code == 409
    with monkeypatch.context() as rotated:
        rotated.setenv("VALHALLA_RESEARCH_IDENTITY_HMAC", "changed-fixture-identity-secret-must-hold")
        assert client.post(f"/api/weweb/customer-research/{new_round}/grant",
                           json={**scope, "user_id": ids["participant"]}, headers=OWNER).status_code == 503
    with Session(engine) as db:
        row, state = customer_research.load(db, round_id, SCOPE)
        assert emails["participant"] not in row.payload_json
        assert state["participants"] and all(not p["answers"] for p in state["participants"].values())
    future = datetime.now(timezone.utc) + timedelta(hours=26)
    monkeypatch.setattr(customer_research, "now", lambda: future)
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    assert client.post(f"{prime}/{round_id}/advance", json=scope).json()["status"] == "RESEARCH_DATA_PURGED"
    assert client.post(f"{prime}/{round_id}/advance", json=scope).json()["status"] == "RESEARCH_DATA_PURGED"
    assert client.get(root, headers=headers).status_code == 404
    with Session(engine) as db:
        _, state = customer_research.load(db, round_id, SCOPE)
        assert state["purged"] and state["participants"] == {} and state["participant_grants"] == []
        assert db.query(LegacyOrchestrationEvent).filter_by(event_type="CUSTOMER_RESEARCH_JOIN_FIXTURE").count() == 0
        assert db.query(LegacyOrchestrationEvent).filter_by(event_type="CUSTOMER_RESEARCH_SUPPRESSION_FIXTURE").count() >= 1


def test_industry_diligence_wakes_specialists_and_keeps_fleet_options_advisory(economic_client):
    from app.models.completion_registry import SourceRegistryItem
    from app.models.foundry_evidence import FoundryEvidence
    from app.services.foundry_discovery import require_current_candidate
    from app.services.foundry_intake import current_time

    client, engine = economic_client
    for model in (SourceRegistryItem, FoundryEvidence):
        model.__table__.create(engine)
    references = {
        "mb-maintenance": "https://www.manitoba.ca/mti/mcd/audits_investigations/audits/maintenance.html",
        "fleetio-pricing": "https://www.fleetio.com/pricing",
        "mta-membership": "https://trucking.mb.ca/membership/member-categories/",
    }
    # Disposable source registry entries. No live connector, client or source account.
    with Session(engine) as db:
        for key, citation in references.items():
            db.add(SourceRegistryItem(source_id=key, canonical_name=key, source_type="INDUSTRY_REFERENCE",
                data_class="live", jurisdiction="CA-MB", citation_ref=citation, permission_status="public",
                license_status="consented_internal_use", governance_status="approved", terminal_state="PASS",
                mode_allowlist_json='["practice"]'))
        db.commit()
    today = current_time().date()
    expires = (today + timedelta(days=15)).isoformat()
    root = "/api/prime/foundry"
    post(client, "mandates", mandate(today))
    for role in ("ODIN", "NJORD"):
        enrollment = client.post("/api/prime/pantheon/assignments", headers=OWNER, json={
            **SCOPE, "assignment_id": str(uuid4()), "role": role, "cadence_seconds": 600, "duration_seconds": 3600,
        })
        assert enrollment.status_code == 201, enrollment.text
    options = [
        {"kind": "BUILD", "setup_minor": 30000, "monthly_minor": 3500, "setup_hours": 60,
         "monthly_hours": 6, "loaded_hour_minor": 6000, "dependencies": ["Tenant-safe import and export", "Support delegate"],
         "estimate_basis": "Scenario only. Build, maintain and support a narrow export tool."},
        {"kind": "BUY", "setup_minor": 10000, "monthly_minor": 2500, "setup_hours": 6,
         "monthly_hours": 2, "loaded_hour_minor": 6000, "dependencies": ["Customer-owned vendor account", "Scoped operator"],
         "estimate_basis": "Scenario only. Customer carries the platform subscription; check access and data export."},
    ]
    study = {"scope": SCOPE, "execution_options": options, "findings": [
        {"facet": facet, "source_id": src, "citation": references[src], "observed_on": today.isoformat(),
         "valid_through": expires, "summary": summary}
        for facet, src, summary in (
            ("REGULATION", "mb-maintenance", "Manitoba describes scheduled vehicle maintenance and inspection records."),
            ("FAILURE_MODES", "mb-maintenance", "Incomplete repair or inspection records can leave audit evidence gaps."),
            ("COMPETITION", "fleetio-pricing", "An incumbent offers tiered per-asset subscriptions with annual commitment options."),
            ("DISTRIBUTION", "mta-membership", "Industry association categories include for-hire and private fleet operators."),
        )
    ]}
    ids = []
    for key, kind in (("managed-fleet-setup", "SERVICE"), ("fleet-audit-export", "SAAS")):
        evidence_id = str(uuid4())
        ids.append(evidence_id)
        evidence = {**SCOPE, "evidence_id": evidence_id, "kind": kind, "evidence_class": "OPERATOR_REPORTED",
                    "title": key, "source_ref": key, "observed_on": today.isoformat(), "expires_on": expires,
                    "currency": "CAD", "unit_price": 15000, "variable_cost_per_unit": 4000,
                    "acquisition_cost_per_unit": 2000, "monthly_fixed_cost": 2000, "monthly_units": 4,
                    "startup_capital": 15000, "test_cost": 0, "rights_attestation": "AUTHORIZED_INTERNAL_RESEARCH"}
        assert client.post(root + "/evidence", json=evidence, headers=OWNER).status_code == 201
        route = f"{root}/evidence/{evidence_id}/industry-diligence"
        denied = client.post(route, json=study)
        assert denied.status_code == 401
        assert client.post(route, headers=OWNER, json={**study, "scope": MIRROR}).status_code == 409
        wrong_citation = {**study, "findings": [{**study["findings"][0],
            "citation": "https://example.invalid/other"}, *study["findings"][1:]]}
        assert client.post(route, headers=OWNER, json=wrong_citation).status_code == 409
        expired = {**study, "findings": [{**study["findings"][0],
            "valid_through": (today - timedelta(days=1)).isoformat()}, *study["findings"][1:]]}
        assert client.post(route, headers=OWNER, json=expired).status_code == 409
        saved = client.post(route, headers=OWNER, json=study)
        assert saved.status_code == 201, saved.text
        result = saved.json()
        assert result["research_status"] == "MORE_RESEARCH_REQUIRED"
        assert "CUSTOMER_NEEDS" in result["missing_facets"] and result["customer_demand_verified"] is False
        assert {x["kind"]: x["year_one_cost_minor"] for x in result["execution_options"]} == {"BUILD": 864000, "BUY": 220000}
        reordered = {**study, "findings": study["findings"][::-1]}
        assert client.post(route, headers=OWNER, json=reordered).json() == result
        changed = {**study, "findings": [{**study["findings"][0], "summary": "A different source assertion to review."}, *study["findings"][1:]]}
        assert client.post(route, headers=OWNER, json=changed).status_code == 409
        post(client, "opportunities", option(today, key, origin="FOUNDRY", foundry_evidence_id=evidence_id))

    with Session(engine) as db:
        assert db.query(SpecialistTrigger).filter(SpecialistTrigger.event_id.startswith("FOUNDRY-INDUSTRY-")).count() == 4
        for role in ("ODIN", "NJORD"):
            report_id = run_assignment(db, role)["report_event_id"]
            report = client.get(f"/api/prime/pantheon/reports/{report_id}").json()
            assert report["trigger"] == "INDUSTRY_DILIGENCE"
            assert {s["evidence_id"] for s in report["observations"]["foundry_signals"]} == set(ids)
            focus = report["observations"]["foundry_signals"][0]["industry_research_focus"]
            assert ("COMPETITION" if role == "ODIN" else "FAILURE_MODES") in focus["review_facets"]
    candidate_url = f"{root}/reports/{report_id}/candidate/{ids[0]}"
    candidate = client.get(candidate_url).json()["proposal"]
    with Session(engine) as db:
        require_current_candidate(db, candidate, SCOPE, today, advisory_only=True)
        with pytest.raises(HTTPException, match="separately verified"):
            require_current_candidate(db, candidate, SCOPE, today)
    response = client.post(f"/api/prime/pantheon/reports/{report_id}/challenge")
    assert response.status_code == 201, response.text
    review_id = response.json()["review_id"]
    queue = client.get("/loki/worker/reviews", headers=REVIEWER, params={"artifact_type": "pantheon_report"})
    digest_bound = next(item for item in queue.json() if item["review_id"] == review_id)
    findings = challenge(digest_bound).model_dump(mode="json")
    receipt = client.post(f"/loki/worker/reviews/{review_id}/result", headers=REVIEWER, json=findings)
    assert receipt.status_code == 201 and any(f["category"] == "industry_execution_uncertainty" for f in findings["findings"])
    assessment = post(client, "assessment", SCOPE, 200)
    assert assessment["opportunity_selection"]["decision"] == "ABSTAIN"
    assert all("INDUSTRY_DEMAND_UNVERIFIED" in x["blockers"] for x in assessment["alternatives"])
    with Session(engine) as db:
        db.query(SourceRegistryItem).filter_by(source_id="mb-maintenance").one().active = False
        db.commit()
    assert client.get(candidate_url).status_code == 409
    after = post(client, "assessment", SCOPE, 200)
    assert all("FOUNDRY_SOURCE_UNAVAILABLE" in x["blockers"] for x in after["alternatives"])
