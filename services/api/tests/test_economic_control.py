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
from app.models.specialist_assignment import SpecialistAssignment
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
                  EconomicPool, EconomicRecord, RevenueLedger, SpecialistAssignment, LokiReview, LokiFinding,
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
