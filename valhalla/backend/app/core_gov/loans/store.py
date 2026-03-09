from __future__ import annotations

from pathlib import Path
import datetime as dt
import uuid
from typing import Any

from app.core_gov.storage.json_store import read_json, write_json

LOANS_PATH = Path("data") / "loans.json"


def _now_utc() -> str:
    return dt.datetime.utcnow().isoformat() + "Z"


def load_loans() -> list[dict[str, Any]]:
    raw = read_json(LOANS_PATH)
    if not raw:
        return []
    items = raw.get("items", [])
    return items if isinstance(items, list) else []


def save_loans(items: list[dict[str, Any]]) -> None:
    write_json(LOANS_PATH, {"items": items})


def add_loan(payload: dict[str, Any]) -> dict[str, Any]:
    items = load_loans()
    now = _now_utc()
    l = {**payload, "id": str(uuid.uuid4()), "created_at_utc": now, "updated_at_utc": now}
    items.append(l)
    if len(items) > 20000:
        items = items[-20000:]
    save_loans(items)
    return l


def get_loan(loan_id: str) -> dict[str, Any] | None:
    for l in load_loans():
        if l.get("id") == loan_id:
            return l
    return None


def list_loans(
    q: str | None = None,
    country: str | None = None,
    province_state: str | None = None,
    product_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    items = load_loans()

    def match(l: dict[str, Any]) -> bool:
        if country and (l.get("country") or "").upper() != country.upper():
            return False
        if province_state and (l.get("province_state") or "").upper() != province_state.upper():
            return False
        if product_type and (l.get("product_type") or "").lower() != product_type.lower():
            return False
        if q:
            s = f"{l.get('name','')} {l.get('lender','')} {l.get('notes','')}".lower()
            if q.lower() not in s:
                return False
        return True

    out = [l for l in items if match(l)]
    out = out[::-1]
    return out[:limit]
