from __future__ import annotations

from app.compliance.eia_exit_handoff import (
    validate_eia_exit_handoff,
    execute_eia_exit_handoff,
)


def test_exit_validation_blocks_when_missing_requirements():
    result = validate_eia_exit_handoff(
        {
            "audit_selfcheck_passed": False,
            "reserve_floor_met": False,
            "founder_approved": False,
            "accountant_review_ready": False,
        }
    )
    assert result["can_exit_eia_mode"] is False
    assert result["blocker_count"] >= 1


def test_exit_execution_succeeds_when_requirements_met():
    result = execute_eia_exit_handoff(
        {
            "audit_selfcheck_passed": True,
            "reserve_floor_met": True,
            "founder_approved": True,
            "accountant_review_ready": True,
            "updated_by": "test_runner",
        }
    )
    assert result["success"] is True
    assert result["state"]["mode"] == "STANDARD"
