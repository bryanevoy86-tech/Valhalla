from __future__ import annotations

from typing import Any


def get_system_state() -> dict[str, Any]:
    """
    Central system state for Heimdall + frontend.
    Keep this simple for V1. Expand later if needed.
    """

    mode = "SAFE"  # SAFE or LIVE

    blockers: list[str] = []
    warnings: list[str] = []

    # --- Example checks (expand later if needed) ---

    # Blocker example:
    # blockers.append("Missing API key for live messaging")

    # Warning example:
    # warnings.append("Low contact volume")

    return {
        "mode": mode,
        "can_execute_live_actions": mode == "LIVE" and len(blockers) == 0,
        "blockers": blockers,
        "warnings": warnings,
    }
