"""Decision analytics - spike detection and drift signals from audit log."""
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

from .log_tail import tail_lines

AUDIT_PATH = Path("data") / "audit.log"


def decision_stats(last_n: int = 200) -> dict:
    """Analyze decision patterns over last N audit log lines."""
    lines = tail_lines(AUDIT_PATH, max_lines=last_n)
    events = []
    for ln in lines:
        try:
            rec = json.loads(ln)
            events.append(rec.get("event"))
        except Exception:
            continue

    c = Counter(events)
    allow = int(c.get("CONE_ALLOW", 0))
    deny = int(c.get("CONE_DENY", 0))
    total = allow + deny

    deny_rate = (deny / total) if total else 0.0

    # Drift heuristics (simple + safe)
    warnings = []
    if total >= 20 and deny_rate >= 0.35:
        warnings.append(
            f"High deny rate detected: {deny}/{total} ({deny_rate:.0%}). "
            f"Possible drift or mis-wiring."
        )
    if deny >= 10 and allow == 0:
        warnings.append(
            "All recent decisions are denied. Something is blocked or misconfigured."
        )

    return {
        "window": {"lines": last_n},
        "counts": {"allow": allow, "deny": deny, "total": total},
        "deny_rate": deny_rate,
        "warnings": warnings,
    }
