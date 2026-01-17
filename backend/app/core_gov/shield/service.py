from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_config() -> Dict[str, Any]:
    return store.read_config()


def update_config(patch: Dict[str, Any]) -> Dict[str, Any]:
    cfg = store.read_config()
    for k in ["enabled", "tier", "reserve_floor", "min_deals_pipeline", "notes", "actions_by_tier"]:
        if k in patch and patch[k] is not None:
            cfg[k] = patch[k]
    cfg["updated_at"] = _utcnow_iso()
    store.write_config(cfg)
    return cfg


def evaluate(reserves: float, pipeline_deals: int, override_tier: str | None = None) -> Dict[str, Any]:
    cfg = store.read_config()
    enabled = bool(cfg.get("enabled", True))
    tier = cfg.get("tier", "green")
    reasons: List[str] = []
    triggered = False

    if override_tier:
        tier = override_tier
        reasons.append("override_tier applied")
        triggered = True
    elif enabled:
        floor = float(cfg.get("reserve_floor") or 0.0)
        min_pipe = int(cfg.get("min_deals_pipeline") or 0)

        if floor > 0 and reserves < floor:
            triggered = True
            reasons.append(f"reserves {reserves} below floor {floor}")
        if min_pipe > 0 and pipeline_deals < min_pipe:
            triggered = True
            reasons.append(f"pipeline {pipeline_deals} below minimum {min_pipe}")

        # simple escalation heuristic
        if triggered:
            if reserves <= 0 and pipeline_deals == 0:
                tier = "red"
            elif reserves < floor * 0.5 if floor > 0 else False:
                tier = "orange"
            else:
                tier = "yellow"

    actions_by = cfg.get("actions_by_tier") or {}
    actions = actions_by.get(tier, [])

    return {
        "ok": True,
        "tier": tier,
        "enabled": enabled,
        "triggered": bool(triggered),
        "actions": actions,
        "reasons": reasons,
    }
