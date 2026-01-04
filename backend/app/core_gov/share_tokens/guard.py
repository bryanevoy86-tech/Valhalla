from __future__ import annotations
from datetime import date
from typing import Any, Dict, Tuple
from . import store

def check(token: str, scope: str) -> Tuple[bool, str, Dict[str, Any] | None]:
    token = (token or "").strip()
    scope = (scope or "").strip()
    if not token:
        return False, "missing token", None

    items = store.list_tokens()
    rec = next((x for x in items if x.get("token") == token), None)
    if not rec:
        return False, "invalid token", None
    if rec.get("status") != "active":
        return False, "token inactive", rec
    if rec.get("scope") != scope:
        return False, "wrong scope", rec
    exp = (rec.get("expires_on") or "").strip()
    if exp and exp < date.today().isoformat():
        return False, "token expired", rec
    return True, "ok", rec
