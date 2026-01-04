from __future__ import annotations
from typing import Any, Dict, List

def persist(deal_id: str, jurisdiction: str = "CA-MB") -> Dict[str, Any]:
    # scan
    from .service import scan
    try:
        from backend.app.deals import store as dstore  # type: ignore
        deal = dstore.get_deal(deal_id)
    except Exception:
        deal = None
    if not deal:
        return {"ok": False, "error": "deal not found"}

    ruleset = "v1"
    try:
        from backend.app.core_gov.legal_profiles import store as pstore  # type: ignore
        profs = pstore.get().get("profiles") or {}
        ruleset = (profs.get(jurisdiction, {}) or {}).get("ruleset") or "v1"
    except Exception:
        pass

    result = scan(deal=deal, ruleset=ruleset)
    flags = result.get("flags") or []

    # write flags into deal.meta.legal_flags (best-effort)
    try:
        meta = (deal.get("meta") or {})
        meta["legal_flags"] = {"jurisdiction": jurisdiction, "ruleset": ruleset, "flags": flags}
        deal["meta"] = meta
        if hasattr(dstore, "save_deal"):
            dstore.save_deal(deal)
        elif hasattr(dstore, "patch_deal"):
            dstore.patch_deal(deal_id, {"meta": meta})
    except Exception:
        pass

    # also create alerts (best-effort)
    try:
        from backend.app.alerts import store as astore  # type: ignore
        for f in flags[:25]:
            astore.create_alert({"type":"legal", "severity": f.get("level","warning"), "title": f.get("code"), "detail": f.get("msg"), "meta": {"deal_id": deal_id}})
    except Exception:
        pass

    return {"ok": True, "deal_id": deal_id, "jurisdiction": jurisdiction, "flags": flags}
