from __future__ import annotations

from typing import Any, Dict, List


def run_batch(limit: int = 200, threshold: float = 0.92) -> Dict[str, Any]:
    warnings: List[str] = []
    accepted = 0
    attempted = 0
    failures = 0
    details: List[Dict[str, Any]] = []

    try:
        from backend.app.core_gov.bank import service as bsvc  # type: ignore
        txns = bsvc.list_txns(status="new", limit=int(limit or 200))
    except Exception as e:
        return {"accepted": 0, "attempted": 0, "failures": 0, "warnings": [f"bank unavailable: {type(e).__name__}: {e}"], "items": []}

    from backend.app.core_gov.reconcile.auto_accept import auto_accept  # type: ignore

    for t in txns:
        attempted += 1
        out = auto_accept(bank_txn_id=t.get("id",""), threshold=threshold)
        details.append(out)
        if out.get("accepted"):
            accepted += 1
        else:
            failures += 1

    return {"accepted": accepted, "attempted": attempted, "failures": failures, "warnings": warnings, "items": details[:50]}
