import json
from datetime import timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.completion_registry import KnowledgeRegistryItem, LearningFeedbackRecord, LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent
from app.models.foundry_evidence import FoundryEvidence
from app.models.specialist_assignment import SpecialistAssignment
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
    for model in (LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent, SpecialistAssignment, FoundryEvidence, KnowledgeRegistryItem, LearningFeedbackRecord):
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
    for model in (LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent, SpecialistAssignment, FoundryEvidence):
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
