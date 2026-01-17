from __future__ import annotations

from pathlib import Path
import datetime as dt
from typing import Any

try:
    from app.core_gov.storage.json_store import read_json, write_json
except ImportError:
    def read_json(path):
        if not path.exists():
            return {}
        try:
            import json
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def write_json(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(path, "w") as f:
            json.dump(data, f, indent=2)


AUDIT_PATH = Path("data") / "weekly_audits.json"


def _now_utc() -> str:
    return dt.datetime.utcnow().isoformat() + "Z"


def load_audits() -> list[dict[str, Any]]:
    raw = read_json(AUDIT_PATH)
    if not raw:
        return []
    items = raw.get("items", [])
    return items if isinstance(items, list) else []


def append_audit(snapshot: dict[str, Any]) -> dict[str, Any]:
    items = load_audits()
    record = {"created_at_utc": _now_utc(), **snapshot}
    items.append(record)
    # cap
    if len(items) > 500:
        items = items[-500:]
    write_json(AUDIT_PATH, {"items": items})
    return record
