from __future__ import annotations

from pathlib import Path
from typing import Any

DATA_DIR = Path("data")

REQUIRED_FILES = [
    "cone_state.json",
    "audit_log.json",
]

OPTIONAL_FILES = [
    "go_progress.json",
    "go_session.json",
    "weekly_audits.json",
    "leads.json",
    "alerts.json",
    "thresholds.json",
    "capital_usage.json",
]


def anchors_check() -> dict[str, Any]:
    missing_required = []
    missing_optional = []
    present = []

    for f in REQUIRED_FILES:
        p = DATA_DIR / f
        if p.exists():
            present.append(f)
        else:
            missing_required.append(f)

    for f in OPTIONAL_FILES:
        p = DATA_DIR / f
        if p.exists():
            present.append(f)
        else:
            missing_optional.append(f)

    red_flags = []
    if missing_required:
        red_flags.append("Missing required governance files (system may not be durable).")

    # Basic sanity warnings
    if "weekly_audits.json" not in present:
        red_flags.append("No weekly audits yet (cadence not established).")

    if "leads.json" not in present:
        red_flags.append("No leads logged yet (no intake flow exists).")

    return {
        "ok": len(missing_required) == 0,
        "present": sorted(present),
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "red_flags": red_flags,
    }
