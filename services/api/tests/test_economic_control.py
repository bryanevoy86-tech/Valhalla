"""End-to-end economic rehearsal through Prime, existing Loki, and Pantheon."""
from datetime import datetime, timedelta, timezone
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
from app.services.owner_operating_brief import operating_evidence

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
    created = client.post("/api/business-factory/listing-drafts", headers=headers, json={
        **SCOPE, "product_id": "candidate_product", "industry": "digital_products",
        "title": "Scoped internal product", "description": "Candidate for a private economic containment rehearsal.",
        "price_cents_cad": 600, "request_key": "econ-contained-fixture",
    })
    assert created.status_code == 200, created.text
    action_id = created.json()["action_id"]
    approve = client.post(f"/api/business-factory/actions/{action_id}/approve",
                          headers=headers, json={"confirmation": "APPROVE_INTERNAL_DRAFT"})
    assert approve.status_code == 200, approve.text
    freeze = {"id": str(uuid4()), "scope": SCOPE, "rationale": "Stop further commitments until the issue is understood."}
    assert client.post(f"{ROOT}/containment", json=freeze).status_code == 401
    receipt = post(client, "containment", freeze)
    assert post(client, "containment", freeze) == receipt
    with Session(engine) as db:
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
    post(client, "mandates", mandate(today))
    post(client, "performance", performance(today))
    post(client, "liquidity", liquidity(today))
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
        "source_ref": "fixture:workshop survey Nov", "observed_on": today.isoformat(),
        "expires_on": (today + timedelta(days=3)).isoformat(), "currency": "CAD",
        "unit_price": 50, "variable_cost_per_unit": 10, "acquisition_cost_per_unit": 10,
        "monthly_fixed_cost": 75, "monthly_units": 10, "startup_capital": 120, "test_cost": 8,
        "rights_attestation": "AUTHORIZED_INTERNAL_RESEARCH",
    }
    job = {"evidence": evidence, "source_id": "regional-buyer-sample", "external_key": "CalibrationSurvey",
           "adapter": "DEMAND_EXPORT", "buyer_segment": "Independent repair shops",
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
    with Session(engine) as db:
        db.query(SourceRegistryItem).filter_by(source_id="regional-buyer-sample").one().active = False
        db.commit()
    assert client.get(f"/api/prime/foundry/reports/{report_id}/candidate/{evidence['evidence_id']}").status_code == 409


def test_statement_continuity_quarantine_and_fixture_asset_recovery(economic_client):
    from app.finops.models import VaultBalance
    from app.models.treasury_reconciliation import StatementAccount, StatementEntry, StatementImport

    client, engine = economic_client
    for model in (StatementAccount, StatementEntry, StatementImport, VaultBalance):
        model.__table__.create(engine)
    today = datetime.now(timezone.utc).date()
    earlier = today - timedelta(days=1)
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

    post(client, "mandates", mandate(today))
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

    viable_id = requests["viable-case"]["evidence_id"]
    assert client.delete(f"{root}/evidence/{viable_id}", headers=OWNER).status_code == 200
    with Session(engine) as db:
        assert [run_due_schedule(db, now=at + timedelta(seconds=301))["status"] for _ in schedules] == ["evaluated", "evaluated"]
    updated = client.get(f"{schedule_root}/{schedules['viable-case']}").json()["latest_report"]
    assert updated["recommendation"]["heimdall_decision"] == "HOLD"
    assert "FOUNDRY_SOURCE_NO_LONGER_CURRENT" in updated["operating_reassessment"]["blockers"]
    assert post(client, "assessment", SCOPE, 200)["best_eligible_alternative_key"] is None
    with Session(engine) as db:
        assert db.query(RevenueLedger).count() == 0


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
