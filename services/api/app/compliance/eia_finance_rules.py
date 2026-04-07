from __future__ import annotations

from typing import Any

from app.compliance.eia_mode_controller import get_compliance_mode_state


def evaluate_eia_finance_restrictions(intent_data: dict[str, Any]) -> dict[str, Any]:
    state = get_compliance_mode_state()
    if not state.get("eia_mode_active", False):
        return {
            "blocked": False,
            "reasons": [],
            "mode": state["mode"],
        }

    purpose = str(intent_data.get("purpose", "") or "").lower()
    payee = str(intent_data.get("payee", "") or "").lower()

    blocked_reasons: list[str] = []

    personal_keywords = [
        "owner_draw",
        "personal_transfer",
        "household",
        "personal_expense",
        "founder_draw",
    ]

    if any(k in purpose for k in personal_keywords):
        blocked_reasons.append("Personal draw or personal transfer blocked in EIA mode")

    if any(k in payee for k in ["bryan", "personal", "household"]):
        blocked_reasons.append("Direct personal payee blocked in EIA mode")

    return {
        "blocked": len(blocked_reasons) > 0,
        "reasons": blocked_reasons,
        "mode": state["mode"],
    }
