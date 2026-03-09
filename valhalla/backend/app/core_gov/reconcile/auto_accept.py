from __future__ import annotations

from typing import Any, Dict, List


def auto_accept(bank_txn_id: str, threshold: float = 0.92, amount_tolerance: float = 1.0, days_tolerance: int = 5) -> Dict[str, Any]:
    warnings: List[str] = []
    try:
        from backend.app.core_gov.reconcile import service as rsvc  # type: ignore
        sug = rsvc.suggest(bank_txn_id=bank_txn_id, max_suggestions=5, amount_tolerance=amount_tolerance, days_tolerance=days_tolerance)
    except Exception as e:
        return {"bank_txn_id": bank_txn_id, "accepted": False, "warnings": [f"reconcile unavailable: {type(e).__name__}: {e}"], "link": {}}

    s = (sug or {}).get("suggestions") or []
    if not s:
        return {"bank_txn_id": bank_txn_id, "accepted": False, "warnings": ["no suggestions"], "link": {}}

    top = s[0]
    score = float(top.get("score") or 0.0)
    if score < float(threshold or 0.92):
        return {"bank_txn_id": bank_txn_id, "accepted": False, "warnings": [f"top score below threshold: {score:.2f} < {threshold:.2f}"], "top": top, "link": {}}

    try:
        link = rsvc.link(bank_txn_id=bank_txn_id, target_type=top.get("target_type"), target_id=top.get("target_id"), note=f"auto-accepted score={score:.2f}", meta={"auto_accept": {"threshold": threshold, "score": score}})
        return {"bank_txn_id": bank_txn_id, "accepted": True, "warnings": warnings, "top": top, "link": link}
    except Exception as e:
        return {"bank_txn_id": bank_txn_id, "accepted": False, "warnings": [f"link failed: {type(e).__name__}: {e}"], "top": top, "link": {}}
