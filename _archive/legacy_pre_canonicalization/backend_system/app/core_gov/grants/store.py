from __future__ import annotations

from pathlib import Path
import datetime as dt
import uuid
from typing import Any

from app.core_gov.storage.json_store import read_json, write_json

GRANTS_PATH = Path("data") / "grants.json"


def _now_utc() -> str:
    return dt.datetime.utcnow().isoformat() + "Z"


def load_grants() -> list[dict[str, Any]]:
    raw = read_json(GRANTS_PATH)
    if not raw:
        return []
    items = raw.get("items", [])
    return items if isinstance(items, list) else []


def save_grants(items: list[dict[str, Any]]) -> None:
    write_json(GRANTS_PATH, {"items": items})


def add_grant(payload: dict[str, Any]) -> dict[str, Any]:
    items = load_grants()
    now = _now_utc()
    g = {**payload, "id": str(uuid.uuid4()), "created_at_utc": now, "updated_at_utc": now}
    items.append(g)
    if len(items) > 20000:
        items = items[-20000:]
    save_grants(items)
    return g


def get_grant(grant_id: str) -> dict[str, Any] | None:
    for g in load_grants():
        if g.get("id") == grant_id:
            return g
    return None


def list_grants(
    q: str | None = None,
    country: str | None = None,
    province_state: str | None = None,
    category: str | None = None,
    stage: str | None = None,
    has_deadline: bool | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    items = load_grants()

    def match(g: dict[str, Any]) -> bool:
        if country and (g.get("country") or "").upper() != country.upper():
            return False
        if province_state and (g.get("province_state") or "").upper() != province_state.upper():
            return False
        if category and (g.get("category") or "").lower() != category.lower():
            return False
        if stage and (g.get("stage") or "").lower() != stage.lower():
            return False
        if has_deadline is True and not g.get("deadline_utc"):
            return False
        if has_deadline is False and g.get("deadline_utc"):
            return False
        if q:
            s = f"{g.get('name','')} {g.get('provider','')} {g.get('eligibility_notes','')} {g.get('notes','')}".lower()
            if q.lower() not in s:
                return False
        return True

    out = [g for g in items if match(g)]
    # most recent first
    out = out[::-1]
    return out[:limit]
