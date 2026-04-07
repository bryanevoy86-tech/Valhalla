from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from app.compliance.eia_mode_controller import get_compliance_mode_state, set_compliance_mode


def validate_eia_exit_handoff(payload: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []

    audit_selfcheck_passed = bool(payload.get("audit_selfcheck_passed", False))
    reserve_floor_met = bool(payload.get("reserve_floor_met", False))
    founder_approved = bool(payload.get("founder_approved", False))
    accountant_review_ready = bool(payload.get("accountant_review_ready", False))

    if not audit_selfcheck_passed:
        blockers.append("Audit self-check has not passed")

    if not reserve_floor_met:
        blockers.append("Reserve floor has not been met")

    if not founder_approved:
        blockers.append("Founder approval missing")

    if not accountant_review_ready:
        blockers.append("Accountant review not marked ready")

    return {
        "can_exit_eia_mode": len(blockers) == 0,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "checked_at": datetime.now(UTC).isoformat(),
    }


def execute_eia_exit_handoff(payload: dict[str, Any]) -> dict[str, Any]:
    validation = validate_eia_exit_handoff(payload)
    if not validation["can_exit_eia_mode"]:
        return {
            "success": False,
            "validation": validation,
            "state": get_compliance_mode_state(),
        }

    updated_by = str(payload.get("updated_by", "manual_exit"))
    new_state = set_compliance_mode("STANDARD", updated_by=updated_by)

    return {
        "success": True,
        "validation": validation,
        "state": new_state,
    }
