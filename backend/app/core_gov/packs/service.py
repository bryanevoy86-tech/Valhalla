from __future__ import annotations

import importlib
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def create_pack(payload: Dict[str, Any]) -> Dict[str, Any]:
    code = _norm(payload.get("code") or "")
    name = _norm(payload.get("name") or "")
    module = _norm(payload.get("module") or "")
    if not code or not name or not module:
        raise ValueError("code, name, module are required")

    router_symbol = _norm(payload.get("router_symbol") or "")
    data_paths = payload.get("data_paths") or []
    if not isinstance(data_paths, list):
        raise ValueError("data_paths must be a list")

    now = _utcnow_iso()
    pid = "pk_" + uuid.uuid4().hex[:12]
    rec = {
        "id": pid,
        "code": code,
        "name": name,
        "module": module,
        "router_symbol": router_symbol,
        "data_paths": [str(x) for x in data_paths],
        "tags": payload.get("tags") or [],
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }

    items = store.list_all()
    items.append(rec)
    store.save_all(items)
    return rec


def list_packs(tag: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_all()
    if tag:
        items = [x for x in items if tag in (x.get("tags") or [])]
    return items


def validate() -> Dict[str, Any]:
    items = store.list_all()
    errors: List[str] = []
    warnings: List[str] = []
    checked = 0

    for p in items:
        checked += 1
        mod = p.get("module") or ""
        sym = p.get("router_symbol") or ""
        try:
            m = importlib.import_module(mod)
        except Exception as e:
            errors.append(f"[{p.get('code')}] import failed: {mod} :: {repr(e)}")
            continue

        if sym:
            if not hasattr(m, sym):
                errors.append(f"[{p.get('code')}] missing router symbol: {mod}.{sym}")

        for dp in (p.get("data_paths") or []):
            # dp is relative path like "backend/data/..."
            if not os.path.exists(dp):
                warnings.append(f"[{p.get('code')}] data path missing (will be created on first use): {dp}")

    ok = len(errors) == 0
    return {"ok": ok, "errors": errors, "warnings": warnings, "checked": checked}
