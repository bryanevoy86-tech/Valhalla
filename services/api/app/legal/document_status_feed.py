from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
QUEUE_DIR = BASE_DIR / "send_queue"
AUDIT_FILE = BASE_DIR / "audit" / "legal_send_audit.jsonl"


def _load_queue_items() -> list[dict[str, Any]]:
    if not QUEUE_DIR.exists():
        return []

    items: list[dict[str, Any]] = []
    for path in sorted(QUEUE_DIR.glob("*.json")):
        try:
            items.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return items


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


def _derive_status(item: dict[str, Any]) -> str:
    approved = bool(item.get("approved", False))
    sent = bool(item.get("sent", False))

    if sent:
        return "sent"
    if approved and not sent:
        return "approved_pending_send"
    if not approved:
        return "queued_pending_approval"
    return "unknown"


def get_document_status_summary() -> dict[str, Any]:
    items = _load_queue_items()
    counts = Counter(_derive_status(item) for item in items)

    return {
        "total_documents": len(items),
        "queued_pending_approval": counts.get("queued_pending_approval", 0),
        "approved_pending_send": counts.get("approved_pending_send", 0),
        "sent": counts.get("sent", 0),
        "unknown": counts.get("unknown", 0),
    }


def get_document_status_feed(limit: int = 100) -> dict[str, Any]:
    items = _load_queue_items()

    rows = []
    for item in items:
        rows.append(
            {
                "approval_id": item.get("approval_id"),
                "template_key": item.get("template_key"),
                "subject": item.get("subject"),
                "document_path": item.get("document_path"),
                "recipients": item.get("recipients", []),
                "cc": item.get("cc", []),
                "approved": bool(item.get("approved", False)),
                "sent": bool(item.get("sent", False)),
                "status": _derive_status(item),
                "created_at": item.get("created_at"),
                "sent_at": item.get("sent_at"),
            }
        )

    rows = sorted(rows, key=lambda x: x.get("created_at") or "", reverse=True)
    return {
        "summary": get_document_status_summary(),
        "items": rows[:limit],
    }


def get_package_history(limit: int = 100) -> dict[str, Any]:
    items = _load_queue_items()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for item in items:
        approval_id = item.get("approval_id", "")
        parts = approval_id.split("__")
        if len(parts) >= 3:
            package_key = f"{parts[0]}__{parts[1]}"
        else:
            package_key = approval_id or "unknown_package"

        grouped[package_key].append(
            {
                "approval_id": approval_id,
                "template_key": item.get("template_key"),
                "status": _derive_status(item),
                "approved": bool(item.get("approved", False)),
                "sent": bool(item.get("sent", False)),
                "created_at": item.get("created_at"),
                "sent_at": item.get("sent_at"),
            }
        )

    packages = []
    for package_id, docs in grouped.items():
        packages.append(
            {
                "package_id": package_id,
                "document_count": len(docs),
                "sent_count": sum(1 for d in docs if d["sent"]),
                "approved_count": sum(1 for d in docs if d["approved"]),
                "pending_count": sum(1 for d in docs if d["status"] == "queued_pending_approval"),
                "documents": docs,
            }
        )

    packages = sorted(
        packages,
        key=lambda x: max((d.get("created_at") or "" for d in x["documents"]), default=""),
        reverse=True,
    )

    return {
        "package_count": len(packages),
        "packages": packages[:limit],
    }


def get_audit_event_feed(limit: int = 200) -> dict[str, Any]:
    events = _load_audit_events()
    events = sorted(events, key=lambda x: x.get("timestamp") or "", reverse=True)
    return {
        "total_events": len(events),
        "events": events[:limit],
    }
