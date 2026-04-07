from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
STATE_DIR = BASE_DIR / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

MODE_FILE = STATE_DIR / "compliance_mode.json"

DEFAULT_STATE = {
    "mode": "EIA_PROTECTED",
    "eia_mode_active": True,
    "personal_draws_allowed": False,
    "eia_packet_required": True,
    "deferred_draw_lock": True,
    "business_only_money_flow": True,
    "manual_override_required_for_exit": True,
    "reserve_floor_required": True,
    "last_updated_at": None,
    "last_updated_by": None,
    "exit_completed_at": None
}


def _write_state(data: dict[str, Any]) -> None:
    MODE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_compliance_mode_state() -> dict[str, Any]:
    if not MODE_FILE.exists():
        state = DEFAULT_STATE.copy()
        state["last_updated_at"] = datetime.now(UTC).isoformat()
        state["last_updated_by"] = "system_init"
        _write_state(state)
        return state
    return json.loads(MODE_FILE.read_text(encoding="utf-8"))


def set_compliance_mode(mode: str, updated_by: str) -> dict[str, Any]:
    mode = mode.strip().upper()
    if mode not in {"EIA_PROTECTED", "STANDARD"}:
        raise ValueError("mode must be EIA_PROTECTED or STANDARD")

    state = get_compliance_mode_state()

    if mode == "EIA_PROTECTED":
        state.update({
            "mode": "EIA_PROTECTED",
            "eia_mode_active": True,
            "personal_draws_allowed": False,
            "eia_packet_required": True,
            "deferred_draw_lock": True,
            "business_only_money_flow": True,
            "manual_override_required_for_exit": True,
            "reserve_floor_required": True,
        })
    else:
        state.update({
            "mode": "STANDARD",
            "eia_mode_active": False,
            "personal_draws_allowed": True,
            "eia_packet_required": False,
            "deferred_draw_lock": False,
            "business_only_money_flow": False,
            "manual_override_required_for_exit": False,
            "reserve_floor_required": False,
            "exit_completed_at": datetime.now(UTC).isoformat(),
        })

    state["last_updated_at"] = datetime.now(UTC).isoformat()
    state["last_updated_by"] = updated_by
    _write_state(state)
    return state


def is_eia_mode_active() -> bool:
    return bool(get_compliance_mode_state().get("eia_mode_active", False))


def personal_draws_allowed() -> bool:
    return bool(get_compliance_mode_state().get("personal_draws_allowed", False))


def eia_packet_required() -> bool:
    return bool(get_compliance_mode_state().get("eia_packet_required", False))


def deferred_draw_lock_active() -> bool:
    return bool(get_compliance_mode_state().get("deferred_draw_lock", False))
