from __future__ import annotations
from typing import Any, Dict, List

def scan_hotlist(limit: int = 25) -> Dict[str, Any]:
    warnings: List[str] = []
    scanned = 0
    try:
        from backend.app.deals import store as dstore  # type: ignore
        deals = dstore.list_deals() if hasattr(dstore, "list_deals") else []
    except Exception as e:
        return {"scanned": 0, "warnings": [f"deals unavailable: {type(e).__name__}"]}

    # v1: scan only active/underwrite/offer stages
    hot = [d for d in deals if (d.get("stage") or "") in ("underwrite","offer","negotiation")]
    hot = hot[:max(1, min(200, int(limit or 25)))]

    try:
        from backend.app.core_gov.legal_filter.persist import persist  # type: ignore
        for d in hot:
            persist(deal_id=d.get("id"), jurisdiction=(d.get("jurisdiction") or "CA-MB"))
            scanned += 1
    except Exception as e:
        warnings.append(f"legal persist failed: {type(e).__name__}: {e}")

    return {"scanned": scanned, "warnings": warnings}
