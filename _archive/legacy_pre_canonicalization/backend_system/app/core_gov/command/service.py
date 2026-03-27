from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

from app.core_gov.cone.service import get_cone_state
from app.core_gov.deals.summary_service import deals_summary
from app.core_gov.followups.store import queue as followup_queue


def _now_utc() -> str:
    return dt.datetime.utcnow().isoformat() + "Z"


def _safe_alerts_snapshot() -> dict[str, Any]:
    # Alerts module may exist; if not, return empty without breaking.
    try:
        from app.core_gov.alerts.store import load_alerts  # type: ignore
        items = load_alerts()
        # keep small
        return {"recent": (items[-10:] if isinstance(items, list) else [])}
    except Exception:
        return {"recent": []}


def what_now(limit: int = 7) -> dict[str, Any]:
    cone = get_cone_state()
    band = cone.band

    summary = deals_summary(limit_scan=2000, top_n=10)
    followups = followup_queue(limit=10, status="open")

    priorities: list[dict[str, Any]] = []

    # Priority 1: overdue followups (if any)
    for fu in followups[:5]:
        priorities.append({
            "type": "followup",
            "priority": fu.get("priority", "medium"),
            "title": f"Follow-up: {fu.get('action')}",
            "why": fu.get("note") or "Open follow-up item",
            "due_at_utc": fu.get("due_at_utc"),
            "id": fu.get("id"),
        })

    # Priority 2: top scored deals → next_actions (already computed)
    for a in summary.get("next_actions", [])[:5]:
        priorities.append({
            "type": "deal_action",
            "priority": a.get("priority", "medium"),
            "title": f"Deal next action: {a.get('action')}",
            "why": a.get("why"),
            "deal_id": a.get("deal_id"),
            "band": a.get("band"),
        })

    # Band guidance
    band_rules = {
        "A": "Expansion allowed. Scale alpha engines with caps + monitoring.",
        "B": "Caution. Execute core actions; avoid reckless scaling; tighten followups.",
        "C": "Stabilize. Only essential actions; reduce risk; focus on cashflow + cleanup.",
        "D": "Survival. Stop non-essential actions; preserve cash; only critical followups.",
    }

    return {
        "now_utc": _now_utc(),
        "band": band,
        "band_guidance": band_rules.get(band, "Follow Cone rules."),
        "priorities": priorities[:limit],
    }


def daily_brief() -> dict[str, Any]:
    cone = get_cone_state()
    summary = deals_summary(limit_scan=3000, top_n=15)
    followups = followup_queue(limit=20, status="open")
    alerts = _safe_alerts_snapshot()

    return {
        "now_utc": _now_utc(),
        "band": cone.band,
        "deals": {
            "counts": summary.get("counts", {}),
            "top_scored": summary.get("top_scored", [])[:10],
            "next_actions": summary.get("next_actions", [])[:10],
        },
        "followups": {"open": followups[:15]},
        "alerts": alerts,
        "recommended_routine": [
            "1) Clear highest-priority followups",
            "2) Execute top 3 deal next-actions",
            "3) Generate offer sheets/disposition packets where appropriate",
            "4) Do a 10-minute systems check (healthz + cone state)",
        ],
    }


def weekly_review() -> dict[str, Any]:
    cone = get_cone_state()
    summary = deals_summary(limit_scan=5000, top_n=20)

    # very lightweight weekly rollup
    counts = summary.get("counts", {})
    by_stage = (counts.get("by_stage") or {})
    by_source = (counts.get("by_source") or {})

    return {
        "now_utc": _now_utc(),
        "band": cone.band,
        "pipeline_rollup": {
            "total_deals_scanned": counts.get("total", 0),
            "by_stage": by_stage,
            "by_source": by_source,
        },
        "top_scored": summary.get("top_scored", [])[:15],
        "focus_next_week": [
            "Increase quality of intake (better lead sources, better qualification).",
            "Improve follow-up completion rate.",
            "Tighten underwriting notes and comps placeholders.",
        ],
        "notes": [
            "This is a v1 review pack; deeper analytics is a later phase pack.",
        ],
    }
