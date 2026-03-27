"""R/Y/G status calculation - health endpoint logic."""
from __future__ import annotations

from pathlib import Path

from ..cone.service import get_cone_state
from ..jobs.router import _JOBS
from ..analytics.decisions import decision_stats
from ..analytics.log_tail import tail_lines
from ..config.thresholds import load_thresholds
from ..notify.queue import push

LOG_PATH = Path("valhalla.log")

def ryg_status() -> dict:
    """Calculate red/yellow/green status with reasons."""
    t = load_thresholds()
    cone = get_cone_state()
    ds = decision_stats(last_n=200)

    failed_jobs = [j for j in _JOBS.values() if j.status == "FAILED"]

    # look for recent unhandled exceptions in log tail
    log_tail = tail_lines(LOG_PATH, max_lines=200)
    unhandled = [ln for ln in log_tail if "UNHANDLED_EXCEPTION" in ln]

    # Determine status
    level = "green"
    reasons = []

    # Cone band influence
    if cone.band in ("C_STABILIZE", "D_SURVIVAL"):
        level = "red"
        reasons.append(f"Cone band is {cone.band} (stabilize/survival).")
    elif cone.band == "B_CAUTION":
        level = "yellow"

    # Jobs thresholds
    if len(failed_jobs) >= t.max_failed_jobs_red and t.max_failed_jobs_red > 0:
        level = "red"
        reasons.append(f"{len(failed_jobs)} failed job(s).")
    elif len(failed_jobs) > t.max_failed_jobs_yellow:
        if level == "green":
            level = "yellow"
        reasons.append(f"{len(failed_jobs)} failed job(s).")

    # Unhandled exceptions threshold
    if len(unhandled) >= t.unhandled_exceptions_red and t.unhandled_exceptions_red > 0:
        level = "red"
        reasons.append(f"{len(unhandled)} unhandled exception(s) in recent logs.")

    # Drift thresholds
    counts = ds.get("counts", {})
    total = int(counts.get("total", 0))
    deny_rate = float(ds.get("deny_rate", 0.0))
    if total >= t.min_decisions_for_drift:
        if deny_rate >= t.deny_rate_red:
            level = "red"
            reasons.append(f"Deny rate red: {deny_rate:.0%}")
        elif deny_rate >= t.deny_rate_yellow:
            if level == "green":
                level = "yellow"
            reasons.append(f"Deny rate yellow: {deny_rate:.0%}")

    # Push notifications for red/yellow (lightweight, non-spam)
    if level == "red":
        push("red", "System Status RED", "; ".join(reasons)[:300], {"cone_band": cone.band})
    elif level == "yellow":
        push("yellow", "System Status YELLOW", "; ".join(reasons)[:300], {"cone_band": cone.band})

    return {
        "status": level,
        "reasons": reasons,
        "cone": cone.model_dump(),
        "jobs": {"total": len(_JOBS), "failed": len(failed_jobs)},
        "decision_stats": ds,
        "thresholds": load_thresholds().model_dump(),
    }
