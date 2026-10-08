from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.engines.actions import CONTRACT_SEND, DISPO_SEND, MONEY_MOVE, OUTREACH, READ_ONLY
from app.core.engines.guard_runtime import enforce_engine
from app.core.engines.states import EngineState
from app.core.policy.gates import autonomy_gate
from app.core.policy.loader import load_policy
from app.core.policy.schemas import DecisionCandidate
from app.models.audit_log import AuditLog
from app.models.engine_state import EngineStateRow
from app.models.go_live_state import GoLiveState
from app.services.go_live import read_state


def _set_engine_state(db, state: EngineState) -> None:
    row = db.query(EngineStateRow).filter(EngineStateRow.engine_name == "wholesaling").first()
    if row is None:
        row = EngineStateRow(engine_name="wholesaling", state=state.value)
    else:
        row.state = state.value
    row.changed_by = "test"
    row.reason = f"autonomy-{state.value.lower()}"
    db.add(row)
    db.commit()


def _set_kill_switch(db, engaged: bool) -> None:
    row = read_state(db)
    row.kill_switch_engaged = engaged
    row.changed_by = "test"
    row.reason = f"kill-switch-{engaged}"
    db.add(row)
    db.commit()


def _isolated_session(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine)

    EngineStateRow.__table__.create(bind=engine, checkfirst=True)
    GoLiveState.__table__.create(bind=engine, checkfirst=True)
    AuditLog.__table__.create(bind=engine, checkfirst=True)

    def fake_get_db_session():
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # Make guard_runtime use this isolated DB for deterministic tests.
    monkeypatch.setattr("app.core.engines.guard_runtime.get_db_session", fake_get_db_session)
    return SessionLocal


def test_l0_to_l3_sample_gate_enforcement():
    policy = load_policy()
    base = {
        "leg": "wholesaling",
        "ev": 0.7,
        "downside": 0.1,
        "confidence_pct": 85,
        "time_to_cash_months": 3,
        "strategic_value": 0.2,
        "proposed_risk_pct_of_capital": 0.5,
        "proposed_exposure_pct_of_leg": 10.0,
        "estimated_variance_pct": 10.0,
    }

    c_l0 = DecisionCandidate(autonomy_level="L0", **base)
    ok_l0, _ = autonomy_gate(c_l0, policy, samples_for_leg=0)
    assert ok_l0 is True

    c_l1 = DecisionCandidate(autonomy_level="L1", **base)
    ok_l1, _ = autonomy_gate(c_l1, policy, samples_for_leg=policy.autonomy.l1_recommend_min_samples)
    assert ok_l1 is True

    c_l2 = DecisionCandidate(autonomy_level="L2", **base)
    ok_l2_fail, reason_l2_fail = autonomy_gate(c_l2, policy, samples_for_leg=policy.autonomy.l2_auto_execute_min_samples - 1)
    assert ok_l2_fail is False
    assert "requires" in reason_l2_fail

    c_l3 = DecisionCandidate(autonomy_level="L3", **base)
    ok_l3_fail, reason_l3_fail = autonomy_gate(c_l3, policy, samples_for_leg=policy.autonomy.l3_auto_scale_min_samples - 1)
    assert ok_l3_fail is False
    assert "requires" in reason_l3_fail


def test_restricted_real_world_actions_blocked_in_sandbox_with_audit(monkeypatch):
    SessionLocal = _isolated_session(monkeypatch)
    db = SessionLocal()
    try:
        _set_engine_state(db, EngineState.SANDBOX)
        _set_kill_switch(db, False)
    finally:
        db.close()

    blocked = []
    for action in (OUTREACH, CONTRACT_SEND, MONEY_MOVE, DISPO_SEND):
        try:
            enforce_engine("wholesaling", action)
            assert False, f"Expected block for {action.name}"
        except HTTPException as exc:
            assert exc.status_code == 409
            detail = exc.detail
            assert detail["type"] == "https://valhalla/errors/engine-blocked"
            assert detail["action"] == action.name
            blocked.append(action.name)

    db = SessionLocal()
    try:
        shadow_rows = db.query(AuditLog).filter(AuditLog.event_type == "shadow_action_blocked").all()
        audit_rows = db.query(AuditLog).filter(AuditLog.event_type == "autonomy_action_blocked").all()
        logged_actions = {row.event_data for row in audit_rows}
        shadow_actions = {row.event_data for row in shadow_rows}
        assert len(shadow_rows) >= len(blocked)
        assert len(audit_rows) >= len(blocked)
        for action in blocked:
            assert any(action in (item or "") for item in logged_actions)
            assert any(action in (item or "") for item in shadow_actions)
        assert any("\"canonical_runtime_mode\": \"SHADOW\"" in (item or "") for item in shadow_actions)
    finally:
        db.close()


def test_restricted_actions_blocked_by_kill_switch_even_when_active(monkeypatch):
    SessionLocal = _isolated_session(monkeypatch)
    db = SessionLocal()
    try:
        _set_engine_state(db, EngineState.ACTIVE)
        _set_kill_switch(db, True)
    finally:
        db.close()

    for action in (OUTREACH, CONTRACT_SEND, MONEY_MOVE, DISPO_SEND):
        try:
            enforce_engine("wholesaling", action)
            assert False, "Expected kill-switch block"
        except HTTPException as exc:
            assert exc.status_code == 409
            assert "Kill switch engaged" in str(exc.detail)


def test_read_only_action_allowed_in_sandbox(monkeypatch):
    SessionLocal = _isolated_session(monkeypatch)
    db = SessionLocal()
    try:
        _set_engine_state(db, EngineState.SANDBOX)
        _set_kill_switch(db, False)
    finally:
        db.close()

    enforce_engine("wholesaling", READ_ONLY)
