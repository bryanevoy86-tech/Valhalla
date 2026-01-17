from __future__ import annotations
import uuid
from typing import Any, Dict, List
from . import store

def create(pattern: str, category: str) -> Dict[str, Any]:
    pattern = (pattern or "").strip().lower()
    category = (category or "").strip().lower()
    if not pattern:
        raise ValueError("pattern required")
    if not category:
        raise ValueError("category required")
    r = {"id": "lr_" + uuid.uuid4().hex[:10], "pattern": pattern, "category": category}
    rules = store.list_rules()
    rules.append(r)
    store.save_rules(rules)
    return r

def apply(description: str) -> str:
    d = (description or "").lower()
    for r in store.list_rules():
        if (r.get("pattern") or "") in d:
            return r.get("category") or ""
    return ""
