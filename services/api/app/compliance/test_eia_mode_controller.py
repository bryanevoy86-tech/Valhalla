from __future__ import annotations

from app.compliance.eia_mode_controller import (
    get_compliance_mode_state,
    set_compliance_mode,
)


def test_default_mode_exists():
    state = get_compliance_mode_state()
    assert "mode" in state
    assert "eia_mode_active" in state


def test_switch_to_standard_mode():
    state = set_compliance_mode("STANDARD", "test_runner")
    assert state["mode"] == "STANDARD"
    assert state["eia_mode_active"] is False
    assert state["personal_draws_allowed"] is True


def test_switch_back_to_eia_mode():
    state = set_compliance_mode("EIA_PROTECTED", "test_runner")
    assert state["mode"] == "EIA_PROTECTED"
    assert state["eia_mode_active"] is True
    assert state["personal_draws_allowed"] is False
