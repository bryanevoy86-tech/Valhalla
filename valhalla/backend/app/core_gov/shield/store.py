from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

DATA_DIR = os.path.join("backend", "data", "shield")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "updated_at": _utcnow_iso(),
                    "config": {
                        "enabled": True,
                        "tier": "green",
                        "reserve_floor": 0.0,
                        "min_deals_pipeline": 0,
                        "notes": "",
                        "actions_by_tier": {
                            "green": ["review_followups"],
                            "yellow": ["audit_expenses", "focus_boring_engines", "review_followups"],
                            "orange": ["pause_expansion", "reduce_marketing", "focus_boring_engines", "review_legal_flags"],
                            "red": ["pause_expansion", "freeze_hiring", "audit_expenses", "manual_override_required"],
                        },
                    },
                },
                f,
                indent=2,
            )


def read_config() -> Dict[str, Any]:
    _ensure()
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("config", {})


def write_config(cfg: Dict[str, Any]) -> None:
    _ensure()
    data = {"updated_at": _utcnow_iso(), "config": cfg}
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, CONFIG_PATH)
