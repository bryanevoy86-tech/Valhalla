import json
from datetime import timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.completion_registry import KnowledgeRegistryItem, LearningFeedbackRecord, LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent
from app.models.foundry_evidence import FoundryEvidence
from app.models.specialist_assignment import SpecialistAssignment, SpecialistTrigger
from app.pantheon.monitor import run_assignment, utc_now
from app.routers.completion_registry import UniversalOpportunityIn, _loki_artifact
from app.services.foundry_discovery import require_current_candidate
from fastapi import HTTPException
import pytest


def test_scoped_foundry_sources_create_role_specific_research_and_reject_revoked_evidence(deal_client, monkeypatch):
    client, engine = deal_client
    owner = {"X-Owner-Mandate-Key": "foundry-source-fixture-owner"}
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", owner["X-Owner-Mandate-Key"])
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    for model in (LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent, SpecialistAssignment, SpecialistTrigger, FoundryEvidence, KnowledgeRegistryItem, LearningFeedbackRecord):
        model.__table__.create(engine)
    scope = {"legacy_instance_id": "discovery-legacy", "business_id": "fixture-venture",
             "jurisdiction": "CA-MB", "engine_id": "micro_saas"}
    with Session(engine) as db:
        db.add(LegacyInstanceRegistryItem(
            legacy_instance_id=scope["legacy_instance_id"], display_name="Discovery fixture", status="PASS",
            synchronization_status="SYNCED", engines_json='["micro_saas"]',
            assigned_businesses_json='["fixture-venture"]', assigned_jurisdictions_json='["CA-MB"]',
            local_knowledge_context_json=json.dumps(scope),
        ))
        db.commit()
    today = utc_now().date()
    payload = {
        **scope, "evidence_id": str(uuid4()), "kind": "SAAS", "evidence_class": "OPERATOR_REPORTED",
        "source_ref": "fixture:market-notes", "title": "Internal scheduling prototype", "observed_on": today.isoformat(),
        "expires_on": (today + timedelta(days=7)).isoformat(), "currency": "CAD",
        "unit_price": 1000, "variable_cost_per_unit": 200, "acquisition_cost_per_unit": 300,
        "monthly_units": 10, "monthly_fixed_cost": 4000, "startup_capital": 3000, "test_cost": 500,
        "rights_attestation": "AUTHORIZED_INTERNAL_RESEARCH",
    }
    root = "/api/prime/foundry"
    assert client.post(f"{root}/evidence", json=payload).status_code == 401
    stored = client.post(f"{root}/evidence", headers=owner, json=payload)
    assert stored.status_code == 201, stored.text
    assert client.post(f"{root}/evidence", headers=owner, json=payload).json() == stored.json()
    for role, expected in (("ODIN", "INVESTIGATE_VOLUME_SENSITIVITY"), ("FREYJA", "VALIDATE_DEMAND_AND_ACQUISITION_COST")):
        request = {**scope, "assignment_id": str(uuid4()), "cadence_seconds": 300, "duration_seconds": 600, "role": role}
        assignment = client.post("/api/prime/pantheon/assignments", headers=owner, json=request)
        assert assignment.status_code == 201, assignment.text
        with Session(engine) as db:
            event_id = run_assignment(db, role)["report_event_id"]
        report = client.get(f"/api/prime/pantheon/reports/{event_id}").json()
        signal = report["observations"]["foundry_signals"][0]
        assert signal["priority"] == expected
        assert signal["economics"]["break_even_units"] == 8
        assert signal["economics"]["estimated_monthly_operating_contribution_minor"] == 1000
        assert signal["economics"]["stress_monthly_operating_contribution_minor"] == -500
        assert signal["economics"]["verified_revenue_minor"] is None

    link = f"{root}/reports/{event_id}/candidate/{payload['evidence_id']}"
    candidate = client.get(link)
    assert candidate.status_code == 200, candidate.text
    assert candidate.json()["execution_authorized"] is False
    proposal = candidate.json()["proposal"]
    evaluation = client.post("/api/completion/phase3/universal-opportunity/evaluate", json={
        "opportunities": [proposal], "shadow_mode": True,
    })
    assert evaluation.status_code == 200, evaluation.text
    with Session(engine) as db:
        reviewed = _loki_artifact(UniversalOpportunityIn.model_validate(proposal))
        require_current_candidate(db, reviewed, scope, today)
        with pytest.raises(HTTPException, match="new source-bound"):
            require_current_candidate(db, {**reviewed, "required_capital": 1}, scope, today)
    assert client.delete(f"{root}/evidence/{payload['evidence_id']}", headers=owner).json()["revoked"]
    assert client.get(link).status_code == 409
    with Session(engine) as db, pytest.raises(HTTPException, match="stale"):
        require_current_candidate(db, reviewed, scope, today)


def test_acquisition_research_stresses_debt_and_requires_funded_equity(deal_client, monkeypatch):
    client, engine = deal_client
    owner = {"X-Owner-Mandate-Key": "foundry-acquisition-owner"}
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", owner["X-Owner-Mandate-Key"])
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    from app.loki.analyst import challenge
    from app.loki.models import LokiFinding, LokiIndependentReceipt, LokiReconsideration, LokiReview
    from app.models.economic_control import EconomicOperation, EconomicPool, EconomicRecord
    from app.models.media_engine import MediaContent
    from app.models.prime_specialist_schedule import PrimeScheduleTrigger, PrimeSpecialistSchedule
    from app.routers.prime_specialist_schedules import run_due_schedule

    for model in (LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent, MediaContent,
                  SpecialistAssignment, SpecialistTrigger, FoundryEvidence, LearningFeedbackRecord, KnowledgeRegistryItem,
                  PrimeSpecialistSchedule, PrimeScheduleTrigger, EconomicPool, EconomicOperation, EconomicRecord,
                  LokiReview, LokiFinding, LokiIndependentReceipt, LokiReconsideration):
        model.__table__.create(engine)
    scope = {"legacy_instance_id": "acquisition-legacy", "business_id": "fixture-venture",
             "jurisdiction": "CA-MB", "engine_id": "acquire"}
    with Session(engine) as db:
        db.add(LegacyInstanceRegistryItem(
            legacy_instance_id=scope["legacy_instance_id"], display_name="Acquisition fixture", status="PASS",
            synchronization_status="SYNCED", engines_json='["acquire"]',
            assigned_businesses_json='["fixture-venture"]', assigned_jurisdictions_json='["CA-MB"]',
            local_knowledge_context_json=json.dumps(scope),
        ))
        db.commit()
    today = utc_now().date()
    request = {
        **scope, "evidence_id": str(uuid4()), "kind": "ACQUISITION", "evidence_class": "SIMULATION",
        "title": "Synthetic acquisition", "source_ref": "fixture:diligence-case", "observed_on": today.isoformat(),
        "expires_on": (today + timedelta(days=1)).isoformat(), "currency": "CAD",
        "unit_price": 1000, "variable_cost_per_unit": 400, "acquisition_cost_per_unit": 0,
        "monthly_fixed_cost": 20000, "monthly_units": 100, "startup_capital": 450000, "test_cost": 1000,
        "rights_attestation": "AUTHORIZED_INTERNAL_RESEARCH",
        "acquisition": {"purchase_price": 1000000, "closing_and_transition_cost": 100000,
                        "funded_working_reserve": 100000, "financed_principal": 750000, "monthly_debt_service": 30000},
    }
    endpoint = "/api/prime/foundry/evidence"
    assert client.post(endpoint, headers=owner, json={**request, "startup_capital": 449999}).status_code == 422
    stored = client.post(endpoint, headers=owner, json=request)
    assert stored.status_code == 201, stored.text
    assignment = client.post("/api/prime/pantheon/assignments", headers=owner, json={
        **scope, "assignment_id": str(uuid4()), "role": "NJORD", "cadence_seconds": 300, "duration_seconds": 600,
    })
    assert assignment.status_code == 201, assignment.text
    with Session(engine) as db:
        report_id = run_assignment(db, "NJORD")["report_event_id"]
    response = client.get(f"/api/prime/pantheon/reports/{report_id}")
    finding = response.json()["observations"]["foundry_signals"][0]
    assert finding["priority"] == "INVESTIGATE_ACQUISITION_DEBT_COVERAGE"
    analysis = finding["economics"]["acquisition"]
    assert analysis["monthly_available_cash_after_debt_minor"] == 10000
    assert analysis["stress_monthly_available_cash_after_debt_minor"] == -5000
    assert analysis["stress_operating_cash_to_debt_service_bp"] == 8333
    assert analysis["debt_inclusive_break_even_units"] == 84
    assert analysis["financing_verified"] is False


    economy = "/api/prime/economy"
    with Session(engine) as db:
        db.add(EconomicPool(currency="CAD"))
        db.commit()

    def capital(path, body, status=201):
        result = client.post(f"{economy}/{path}", headers=owner, json=body)
        assert result.status_code == status, result.text
        return result.json()

    mandate_id = str(uuid4())
    capital("mandates", {
        "id": mandate_id, "scope": scope, "currency": "CAD", "max_exposure": 2000000,
        "max_cumulative_loss": 200000, "max_additional_funding": 900000, "min_operating_reserve": 100000,
        "review_by": (today + timedelta(days=10)).isoformat(), "minimum_period_net": 0,
        "continuation_criteria": "Require positive stressed cash after debt.",
        "suspension_criteria": "Hold if modelled debt cannot be serviced.",
        "exit_criteria": "Stop before any binding purchase.", "obligations": ["Review borrowing assumptions"],
    })
    capital("liquidity", {
        "id": str(uuid4()), "scope": scope, "as_of": today.isoformat(), "receipt_ref": "fixture:acquisition-runway",
        "unrestricted_pool_minor": 1000000, "protected_pool_minor": 2000000, "evidence_class": "RECONCILIATION_FIXTURE",
    })
    capital("performance", {
        "id": str(uuid4()), "scope": scope, "start": today.isoformat(), "end": today.isoformat(),
        "operating_receipts": 100, "operating_costs": 50, "outstanding_exposure": 0,
        "uncommitted_local_cash": 1000000, "receipt_ref": "fixture:acquisition-period",
        "obligations_status": "SATISFIED", "evidence_class": "RECONCILIATION_FIXTURE",
    })
    viable = {**request, "evidence_id": str(uuid4()), "title": "Synthetic paid-up acquisition",
              "source_ref": "fixture:smaller-debt-service",
              "acquisition": {**request["acquisition"], "monthly_debt_service": 20000}}
    assert client.post(endpoint, headers=owner, json=viable).status_code == 201
    with Session(engine) as db:
        source_report = run_assignment(db, "NJORD", now=utc_now() + timedelta(seconds=301))["report_event_id"]

    schedule_root = "/api/prime/specialist-schedules"
    schedules = {}
    for key, source in (("adverse-case", request), ("viable-case", viable)):
        candidate = client.get(f"/api/prime/foundry/reports/{source_report}/candidate/{source['evidence_id']}")
        assert candidate.status_code == 200, candidate.text
        proposal = candidate.json()["proposal"]
        schedule_id = str(uuid4())
        schedules[key] = schedule_id
        response = client.post(schedule_root, headers=owner, json={
            "schedule_id": schedule_id, "business_id": scope["business_id"], "cadence_seconds": 300,
            "duration_seconds": 1800, "opportunity": proposal,
        })
        assert response.status_code == 201, response.text
        capital("opportunities", {
            "id": str(uuid4()), "scope": scope, "opportunity_key": key, "title": source["title"], "origin": "FOUNDRY",
            "status": "CANDIDATE", "evidence_ref": source["source_ref"], "foundry_evidence_id": source["evidence_id"],
            "valid_through": source["expires_on"], "required_capital": 1, "projected_annual_net": 9000000,
            "maximum_downside": 1, "uncertainty_bp": 1000, "demand_bp": 8000, "operational_independence_bp": 8000,
            "time_to_revenue_days": 10, "compliance": "SATISFIED_IN_FIXTURE", "dependencies": [],
            "activation_requirements": ["Authorized diligence only"],
        })
    previous = capital("assessment", scope, 200)
    assert previous["best_eligible_alternative_key"] == "viable-case"
    options = {item["opportunity_key"]: item for item in previous["alternatives"]}
    assert options["viable-case"]["required_capital"] == 450000
    assert options["adverse-case"]["projected_annual_net"] == 120000
    assert "ACQUISITION_DEBT_STRESS_SHORTFALL" in options["adverse-case"]["blockers"]
    at = utc_now() + timedelta(seconds=1)
    with Session(engine) as db:
        assert [run_due_schedule(db, now=at)["status"] for _ in schedules] == ["evaluated", "evaluated"]
    adverse_report = client.get(f"{schedule_root}/{schedules['adverse-case']}").json()["latest_report"]
    good_report = client.get(f"{schedule_root}/{schedules['viable-case']}").json()["latest_report"]
    assert adverse_report["recommendation"]["heimdall_decision"] == "HOLD"
    assert "ACQUISITION_DEBT_STRESS_SHORTFALL" in adverse_report["operating_reassessment"]["blockers"]
    assert good_report["operating_reassessment"]["blockers"] == []
    assert good_report["operating_reassessment"]["source_assessment"]["economics"]["verified_revenue_minor"] is None
    assert good_report["external_authority"] is False
    reviewer = {"X-Loki-Reviewer-Key": "acquisition-separate-review-fixture"}
    monkeypatch.setenv("VALHALLA_LOKI_REVIEWER_KEY", reviewer["X-Loki-Reviewer-Key"])
    monkeypatch.setenv("VALHALLA_LOKI_REVIEWER_ID", "acquisition-separate-reviewer")
    for key in ("adverse-case", "viable-case"):
        plan = {"id": str(uuid4()), "scope": scope, "action": "REDEPLOY", "alternative_key": key,
                "requested_additional_minor": 450000, "rationale": "Practice acquisition diligence only.",
                "past_spend_minor": 0, "assets": []}
        artifact = capital("review-artifact", plan, 200)
        review = client.post("/loki/reviews", json=artifact)
        assert review.status_code == 201, review.text
        review_id = review.json()["id"]
        decision = {"plan": plan, "independent_review_id": review_id,
                    "expected_artifact_sha256": artifact["artifact_sha256"]}
        capital("decisions", decision, 409)
        items = client.get("/loki/worker/reviews", headers=reviewer, params={"artifact_type": "economic_advice"}).json()
        opinion = challenge(next(item for item in items if item["review_id"] == review_id))
        assert client.post(f"/loki/worker/reviews/{review_id}/result", headers=reviewer,
                           json=opinion.model_dump(mode="json")).status_code == 201
        findings = client.get(f"/loki/reviews/{review_id}/findings").json()
        accepted = client.post(f"/loki/reviews/{review_id}/reconsider", headers=owner, json={
            "artifact_sha256": artifact["artifact_sha256"], "disposition": "accept_risk",
            "material_finding_ids": [item["id"] for item in findings],
            "reason": "Acknowledge the evidence for isolated simulation only.",
        })
        if key == "adverse-case":
            assert accepted.status_code == 409
            assert any(finding["severity"] == "critical" for finding in findings)
            rejected = capital("decisions", decision, 409)
            assert "REDEPLOYMENT_ALTERNATIVE_UNJUSTIFIED" in rejected["detail"]["blockers"]
        else:
            assert accepted.status_code == 200, accepted.text
            receipt = capital("decisions", decision)
            assert receipt["reserved_simulation_minor"] == 450000
            assert receipt["execution_authorized"] is False
            assert receipt["actual_recovered_capital_minor"] is None
            assert capital("decisions", decision) == receipt

    enrolled = client.post("/api/prime/pantheon/assignments", headers=owner, json={
        **scope, "assignment_id": str(uuid4()), "role": "MIMIR", "cadence_seconds": 300, "duration_seconds": 600,
    })
    assert enrolled.status_code == 201, enrolled.text
    with Session(engine) as db:
        learning_id = run_assignment(db, "MIMIR")["report_event_id"]
    lesson = client.get(f"/api/prime/pantheon/reports/{learning_id}").json()["observations"]["economic_reassessment"]
    assert lesson["last_internal_decision"]["id"] == receipt["id"]
    assert lesson["verified_real_world_outcome"] is False

    assert client.delete(f"{endpoint}/{viable['evidence_id']}", headers=owner).status_code == 200
    with Session(engine) as db:
        assert [run_due_schedule(db, now=at + timedelta(seconds=301))["status"] for _ in schedules] == ["evaluated", "evaluated"]
    revised = client.get(f"{schedule_root}/{schedules['viable-case']}").json()["latest_report"]
    assert revised["recommendation"]["heimdall_decision"] == "HOLD"
    assert "FOUNDRY_SOURCE_NO_LONGER_CURRENT" in revised["operating_reassessment"]["blockers"]
    assert capital("assessment", scope, 200)["best_eligible_alternative_key"] is None
