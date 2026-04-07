from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
QUEUE_DIR = BASE_DIR / "approval_queue"


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


def get_financial_package_history(limit: int = 100) -> dict[str, Any]:
    items = _load_queue_items()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for item in items:
        intent_id = item.get("intent_id", "")
        parts = intent_id.split("__")
        deal_id = parts[0] if parts else "unknown"
        package_id = f"{deal_id}__finance_package"

        grouped[package_id].append(
            {
                "intent_id": intent_id,
                "deal_id": item.get("deal_id"),
                "purpose": item.get("purpose"),
                "amount": item.get("amount"),
                "approved": item.get("approved", False),
                "blocked": item.get("blocked", False),
                "block_reason": item.get("block_reason"),
                "created_at": item.get("created_at"),
                "approved_at": item.get("approved_at"),
            }
        )

    packages = []
    for package_id, intents in grouped.items():
        packages.append(
            {
                "package_id": package_id,
                "deal_id": intents[0].get("deal_id") if intents else None,
                "intent_count": len(intents),
                "approved_count": sum(1 for i in intents if i.get("approved")),
                "blocked_count": sum(1 for i in intents if i.get("blocked")),
                "pending_count": sum(1 for i in intents if not i.get("approved") and not i.get("blocked")),
                "intents": intents,
            }
        )

    packages = sorted(
        packages,
        key=lambda x: max((i.get("created_at") or "" for i in x["intents"]), default=""),
        reverse=True,
    )

    return {
        "package_count": len(packages),
        "packages": packages[:limit],
    }
