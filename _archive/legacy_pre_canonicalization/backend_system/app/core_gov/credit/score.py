from __future__ import annotations
from typing import Any, Dict
from .tradelines import list_items as list_tradelines
from . import store as pstore

def score() -> Dict[str, Any]:
    prof = pstore.get().get("profile") or {}
    tl = list_tradelines()
    done = len([x for x in tl if x.get("status") in ("open","active","done")])
    todo = len([x for x in tl if x.get("status") == "todo"])
    has_duns = 1 if (prof.get("duns") or "").strip() else 0
    has_site = 1 if (prof.get("website") or "").strip() else 0
    base = 10*has_duns + 10*has_site + 5*done - 2*todo
    return {"score_v1": max(0, min(100, int(base))), "tradelines_done": done, "tradelines_todo": todo, "signals": {"has_duns": bool(has_duns), "has_site": bool(has_site)}}
