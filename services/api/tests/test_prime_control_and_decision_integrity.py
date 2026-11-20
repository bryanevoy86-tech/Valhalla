"""Prime control-plane privacy and real decision integrity regression tests."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.completion_registry import LearningFeedbackRecord, KnowledgeRegistryItem
from app.routers import completion_registry, loki, decision_outcome, model_provider
from app.routers.governance_orchestrator import evaluate_all
from app.schemas.governance import GovernanceEvaluationRequest
from app.services.universal_opportunity_evaluator import evaluate_generic_opportunity


@pytest.mark.parametrize("path", [
    "/api/completion/legacy-instances",
    "/loki/reviews",
    "/heimdall/decisions/outcomes",
    "/system/models/",
])
def test_private_apis_reject_public_builder_and_unconfigured_access(monkeypatch, path):
    app = FastAPI()
    for module in (completion_registry, loki, decision_outcome, model_provider):
        app.include_router(module.router)
    # Authentication must reject before any database access.
    def forbidden_db():
        raise AssertionError("unauthorized request reached the database")
    app.dependency_overrides[get_db] = forbidden_db
    with TestClient(app) as client:
        monkeypatch.delenv("VALHALLA_PRIME_CONTROL_KEY", raising=False)
        assert client.get(path).status_code == 503
        monkeypatch.setenv("VALHALLA_PRIME_CONTROL_KEY", "prime-test-only")
        assert client.get(path).status_code == 401
        assert client.get(path, headers={"X-API-Key": "prime-test-only"}).status_code == 401
        assert client.get(path, headers={"X-Prime-Control-Key": "wrong"}).status_code == 401


def test_valid_private_key_allows_authenticated_request(monkeypatch):
    from app.core.dependencies import require_prime_control_key
    from fastapi import Depends
    monkeypatch.setenv("VALHALLA_PRIME_CONTROL_KEY", "prime-test-only")
    app = FastAPI()

    @app.get("/test-private", dependencies=[Depends(require_prime_control_key)])
    def test_endpoint():
        return {"ok": True}

    with TestClient(app) as client:
        assert client.get("/test-private", headers={"X-Prime-Control-Key": "prime-test-only"}).json() == {"ok": True}


def test_partial_specialist_reports_are_not_external_authority():
    decision = evaluate_all(GovernanceEvaluationRequest(
        context_type="new_vertical", data={}, gods=["odin", "odin"]
    ))
    assert len(decision.checks) == 1
    assert not decision.full_coverage
    assert decision.evaluation_only
    assert not decision.external_effects_authorized


def test_direct_pantheon_blocks_tyr_red_line():
    decision = evaluate_all(GovernanceEvaluationRequest(
        context_type="new_vertical", data={"tax_evasion": "true"}
    ))
    assert decision.full_coverage
    assert not decision.overall_allowed
    assert "tyr" in decision.blocked_by
    assert not decision.external_effects_authorized


def test_mimir_only_reads_scoped_shadow_feedback_and_never_claims_live_success():
    engine = create_engine("sqlite://")
    LearningFeedbackRecord.__table__.create(engine)
    KnowledgeRegistryItem.__table__.create(engine)
    try:
        with Session(engine) as db:
            base = dict(feedback_type="operational_result", domain="ops_automation",
                        jurisdiction="CA-MB", business_scope="legacy-a",
                        outcome_class="SHADOW_OUTCOME")
            for id_, changes in [
                ("good", {"operational_score": .8}),
                ("bad", {"operational_score": .2}),
                ("unknown", {"operational_score": None}),
                ("other-legacy", {"business_scope": "legacy-b", "operational_score": .9}),
                ("other-domain", {"domain": "real_estate", "operational_score": .9}),
                ("other-jurisdiction", {"jurisdiction": "CA-ON", "operational_score": .9}),
                ("claimed-live", {"outcome_class": "VERIFIED_REAL_OUTCOME", "operational_score": .95}),
            ]:
                db.add(LearningFeedbackRecord(feedback_id=id_, **dict(base, **changes)))
            db.commit()
            opp = completion_registry.UniversalOpportunityIn(
                opportunity_id="unit-test", engine_id="ops_automation",
                title="Test opportunity", summary="Test only",
                legacy="legacy-a", jurisdiction="CA-MB",
            )
            result = completion_registry._build_mimir_context(db, opp, "SHADOW_OUTCOME")
            assert result["prior_successes"] == 1
            assert result["prior_failures"] == 1
            ids = {r["id"] for r in result["source_references"]}
            assert ids == {"good", "bad", "unknown"}
            for kind in ("VALHALLA_OUTCOME", "HISTORICAL_OUTCOME"):
                isolated = completion_registry._build_mimir_context(db, opp, kind)
                assert isolated["prior_successes"] == isolated["prior_failures"] == 0
                assert not isolated["source_references"]
    finally:
        engine.dispose()


def opportunity(**changes):
    original = {
        "opportunity_id": "scope-test", "engine_id": "ops_automation",
        "title": "Test", "summary": "Test", "status": "RESEARCHING",
        "required_capital": 10000, "estimated_test_cost": 500,
        "estimated_time_to_first_revenue_days": 30,
        "expected_margin_low": .3, "expected_margin_high": .6,
        "downside_exposure": .1, "automation_potential": .9,
        "scalability": .9, "strategic_value": .9, "evidence_confidence": .95,
        "maximum_capital_exposure": 10000,
        "maximum_tolerable_loss": 1000,
        "available_safe_capital": 15000, "required_reserve_to_survive_failure": 2000,
        "recovery_options": ["CONTAIN"], "exit_options": ["EXIT"],
        "point_of_no_return": {"condition": "deposit", "source": "test",
                                "requires_reapproval_before_crossing": True},
        "specialist_inputs": {},
    }
    return dict(original, **changes)


def evaluate(payload):
    return evaluate_generic_opportunity(payload, decision_model="CHAMPION",
        reveal_historical_outcomes=False, expected_outcome_class="SHADOW_OUTCOME")


@pytest.mark.parametrize("fields", [
    {"expected_margin_low": .8, "expected_margin_high": .2},
    {"maximum_capital_exposure": 5000},
])
def test_loki_rejects_contradictory_proposal_economics(fields):
    result = evaluate(opportunity(**fields))
    assert result["final_decision"] == "reject"
    assert any(
        "CONSISTENCY" in f["objection_id"] and f["severity"] == "critical"
        for f in result["loki_objections"]["items"]
    )
    assert not result["pantheon"]["independent_audit_verified"]


def test_final_risk_gate_and_prediction_always_agree():
    result = evaluate(opportunity(blast_radius="SYSTEMIC"))
    assert result["final_decision"] != "proceed"
    assert result["outcome_contract"]["heimdall_decision"] == result["final_decision"].upper()
    assert result["outcome_contract"]["evidence_snapshot_id"] == result["prediction_snapshot"]["prediction_snapshot_id"]
    assert result["hard_gate_evaluation"]["pass"] is False
    assert not result["pantheon"]["external_effects_authorized"]
    assert not result["pantheon"]["checks"]["tyr"]["allowed"]
    assert not result["pantheon"]["checks"]["forseti"]["allowed"]


@pytest.mark.parametrize("path", [
    "/enable", "/disable", "/kill-switch/engage", "/kill-switch/release",
])
def test_go_live_mutations_require_both_private_and_owner_credentials(monkeypatch, path):
    from app.routers.go_live import router
    monkeypatch.setenv("VALHALLA_PRIME_CONTROL_KEY", "prime-release-test")
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", "owner-release-test")
    monkeypatch.setenv("VALHALLA_FACTORY_KEY", "factory-release-test")
    app = FastAPI()
    app.include_router(router)

    def forbidden_db():
        raise AssertionError("unauthorized request reached the database")
    app.dependency_overrides[get_db] = forbidden_db
    body = {"changed_by": "test", "reason": "isolated auth test"}
    with TestClient(app) as client:
        for headers in ({}, {"X-Prime-Control-Key": "prime-release-test"},
                        {"X-Owner-Mandate-Key": "owner-release-test"},
                        {"X-Prime-Control-Key": "prime-release-test",
                         "X-Owner-Mandate-Key": "factory-release-test"}):
            assert client.post("/governance/go-live" + path,
                               headers=headers, json=body).status_code == 401


@pytest.mark.parametrize("path", ["/state", "/checklist"])
def test_go_live_reads_are_private(monkeypatch, path):
    from app.routers.go_live import router
    monkeypatch.setenv("VALHALLA_PRIME_CONTROL_KEY", "prime-release-test")
    app = FastAPI()
    app.include_router(router)
    def forbidden_db():
        raise AssertionError("unauthorized request reached the database")
    app.dependency_overrides[get_db] = forbidden_db
    with TestClient(app) as client:
        assert client.get("/governance/go-live" + path).status_code == 401


@pytest.mark.parametrize("path", ["/complete", "/incomplete"])
def test_metadata_mutation_requires_both_credentials(monkeypatch, path):
    from app.routers.system_status import router
    monkeypatch.setenv("VALHALLA_PRIME_CONTROL_KEY", "prime-release-test")
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", "owner-release-test")
    app = FastAPI()
    app.include_router(router)
    def forbidden_db():
        raise AssertionError("unauthorized request reached db")
    app.dependency_overrides[get_db] = forbidden_db
    with TestClient(app) as client:
        for headers in ({}, {"X-Prime-Control-Key": "prime-release-test"},
                        {"X-Owner-Mandate-Key": "owner-release-test"}):
            assert client.post("/system/status" + path, headers=headers).status_code == 401


def test_go_live_metadata_cannot_certify_release_and_stop_never_auto_resumes():
    from fastapi import HTTPException
    from app.models.go_live_state import GoLiveState
    from app.models.system_metadata import SystemMetadata
    from app.services.go_live import checklist, set_go_live, set_kill_switch, read_state
    engine = create_engine("sqlite://")
    GoLiveState.__table__.create(engine)
    SystemMetadata.__table__.create(engine)
    try:
        with Session(engine) as db:
            db.add(SystemMetadata(id=1, version="test", backend_complete=True))
            db.commit()
            read_state(db)
            report = checklist(db)
            assert report["required"]["backend_complete"]["ok"]
            assert report["required"]["packs_installed"]["ok"]
            assert not report["ok"]
            assert not report["required"]["operational_release_evidence"]["ok"]
            with pytest.raises(HTTPException) as exc:
                set_go_live(db, True, "test", None)
            assert exc.value.status_code == 412
            row = read_state(db)
            row.go_live_enabled = True  # simulate an old persisted state
            db.commit()
            row = set_kill_switch(db, True, "test", None)
            assert row.kill_switch_engaged and not row.go_live_enabled
            assert not checklist(db)["required"]["emergency_stop_clear"]["ok"]
            row = set_kill_switch(db, False, "test", None)
            assert not row.kill_switch_engaged and not row.go_live_enabled
            with pytest.raises(ValueError):
                set_go_live(db, "false", "test", None)
            with pytest.raises(ValueError):
                set_kill_switch(db, "false", "test", None)
    finally:
        engine.dispose()
