from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
QUEUE_DIR = BASE_DIR / "approval_queue"
AUDIT_FILE = BASE_DIR / "audit" / "finance_audit.jsonl"


def _load_queue_items() -> list[dict[str, Any]]:
    if not QUEUE_DIR.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(QUEUE_DIR.glob("*.json")):
        try:
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return rows


def _load_audit_events() -> list[dict[str, Any]]:
    if not AUDIT_FILE.exists():
        return []
    rows: list[dict[str, Any]] = []
    with AUDIT_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def get_finance_status_summary() -> dict[str, Any]:
    items = _load_queue_items()
    counts = Counter()

    for item in items:
        if item.get("blocked"):
            counts["blocked"] += 1
        elif item.get("approved"):
            counts["approved"] += 1
        else:
            counts["pending"] += 1

    return {
        "total_items": len(items),
        "pending": counts.get("pending", 0),
        "approved": counts.get("approved", 0),
        "blocked": counts.get("blocked", 0),
    }


def get_finance_status_feed(limit: int = 100) -> dict[str, Any]:
    items = _load_queue_items()
    items = sorted(items, key=lambda x: x.get("created_at") or "", reverse=True)
    return {
        "summary": get_finance_status_summary(),
        "items": items[:limit],
    }


def get_finance_audit_feed(limit: int = 200) -> dict[str, Any]:
    events = _load_audit_events()
    events = sorted(events, key=lambda x: x.get("timestamp") or "", reverse=True)
    return {
        "total_events": len(events),
        "events": events[:limit],
    }
