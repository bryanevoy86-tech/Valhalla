from __future__ import annotations
from typing import Any, Dict, List
from .tradelines import list_items as list_tradelines
from . import store as pstore

def recommend() -> Dict[str, Any]:
    prof = pstore.get().get("profile") or {}
    steps: List[str] = []
    if not (prof.get("website") or "").strip():
        steps.append("Add business website to credit profile")
    if not (prof.get("duns") or "").strip():
        steps.append("Create/confirm D-U-N-S number")
    tl = list_tradelines()
    if len(tl) < 3:
        steps.append("Add 3 starter tradelines (net30 vendors)")
    if any(x.get("status") == "todo" for x in tl):
        steps.append("Complete TODO tradelines and mark status open/done")
    return {"steps": steps[:10]}
