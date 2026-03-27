from __future__ import annotations
from typing import Any, Dict, List

def report() -> Dict[str, Any]:
    obligations = []
    try:
        from backend.app.core_gov.budget_obligations import store as obstore
        obligations = [x for x in obstore.list_items() if x.get("status") == "active"]
    except Exception:
        obligations = []

    ver = {}
    try:
        from backend.app.core_gov.autopay_verify import store as vstore
        for x in vstore.list_items():
            ver[x.get("obligation_id")] = x
    except Exception:
        ver = {}

    gaps: List[Dict[str, Any]] = []
    for ob in obligations:
        if not bool(ob.get("autopay")):
            continue
        oid = ob.get("id")
        v = ver.get(oid)
        if not v or not bool(v.get("verified")):
            gaps.append({"obligation": ob, "verification": v or None})

    gaps.sort(key=lambda x: (x["obligation"].get("name","")))
    return {"count": len(gaps), "gaps": gaps[:2000]}
