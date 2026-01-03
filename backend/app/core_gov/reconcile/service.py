from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from . import store


def _parse_date(s: str) -> Optional[date]:
    try:
        return date.fromisoformat((s or "").strip())
    except Exception:
        return None


def _abs(x: float) -> float:
    return x if x >= 0 else -x


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe(fn, warnings: List[str], label: str):
    try:
        return fn()
    except Exception as e:
        warnings.append(f"{label} unavailable: {type(e).__name__}: {e}")
        return None


def suggest(bank_txn_id: str, max_suggestions: int = 10, amount_tolerance: float = 1.0, days_tolerance: int = 5) -> Dict[str, Any]:
    warnings: List[str] = []

    def _get_txn():
        from backend.app.core_gov.bank import service as bsvc  # type: ignore
        return bsvc.get_one(bank_txn_id)
    txn = _safe(_get_txn, warnings, "bank") or None
    if not txn:
        return {"bank_txn_id": bank_txn_id, "suggestions": [], "warnings": warnings + ["bank txn not found"]}

    t_date = _parse_date(txn.get("date",""))
    t_amt = float(txn.get("amount") or 0.0)
    t_desc = (txn.get("description") or "").lower()

    suggestions: List[Dict[str, Any]] = []

    # payments
    def _payments():
        from backend.app.core_gov.budget import store as bstore  # type: ignore
        return bstore.list_payments()
    pays = _safe(_payments, warnings, "budget_payments") or []
    for p in pays:
        pd = _parse_date(p.get("paid_date",""))
        pa = float(p.get("amount") or 0.0)
        if _abs(pa - t_amt) > float(amount_tolerance or 1.0):
            continue
        if t_date and pd:
            if _abs((pd - t_date).days) > int(days_tolerance or 5):
                continue
            day_score = 1.0 - (min(_abs((pd - t_date).days), int(days_tolerance or 5)) / float(days_tolerance or 5))
        else:
            day_score = 0.4
        amt_score = 1.0 - (min(_abs(pa - t_amt), float(amount_tolerance or 1.0)) / float(amount_tolerance or 1.0))
        score = 0.65 * amt_score + 0.35 * day_score
        suggestions.append({
            "target_type": "payment",
            "target_id": p.get("id",""),
            "date": p.get("paid_date",""),
            "amount": pa,
            "score": float(score),
            "reason": "amount+date match vs payment",
            "snapshot": p,
        })

    # receipts
    def _receipts():
        from backend.app.core_gov.receipts import service as rsvc  # type: ignore
        return rsvc.list_items()
    rcs = _safe(_receipts, warnings, "receipts") or []
    for r in rcs:
        rd = _parse_date(r.get("date",""))
        ra = float(r.get("total") or 0.0)
        if _abs(ra - t_amt) > float(amount_tolerance or 1.0):
            continue
        if t_date and rd:
            if _abs((rd - t_date).days) > int(days_tolerance or 5):
                continue
            day_score = 1.0 - (min(_abs((rd - t_date).days), int(days_tolerance or 5)) / float(days_tolerance or 5))
        else:
            day_score = 0.4
        amt_score = 1.0 - (min(_abs(ra - t_amt), float(amount_tolerance or 1.0)) / float(amount_tolerance or 1.0))
        # vendor/desc boost
        vendor = (r.get("vendor") or "").lower()
        desc_boost = 0.15 if (vendor and (vendor in t_desc or t_desc in vendor)) else 0.0
        score = min(1.0, 0.6 * amt_score + 0.3 * day_score + desc_boost)
        suggestions.append({
            "target_type": "receipt",
            "target_id": r.get("id",""),
            "date": r.get("date",""),
            "amount": ra,
            "score": float(score),
            "reason": "amount+date match vs receipt (+vendor boost if any)",
            "snapshot": r,
        })

    suggestions.sort(key=lambda x: float(x.get("score") or 0.0), reverse=True)
    return {"bank_txn_id": bank_txn_id, "suggestions": suggestions[: int(max_suggestions or 10)], "warnings": warnings}


def link(bank_txn_id: str, target_type: str, target_id: str, note: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    if target_type not in ("payment", "receipt", "unknown"):
        raise ValueError("target_type must be payment|receipt|unknown")
    if not bank_txn_id:
        raise ValueError("bank_txn_id required")
    if not target_id:
        raise ValueError("target_id required")

    rec = {
        "id": "rl_" + uuid.uuid4().hex[:12],
        "bank_txn_id": bank_txn_id,
        "target_type": target_type,
        "target_id": target_id,
        "note": note or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
    }
    items = store.list_links()
    items.append(rec)
    store.save_links(items)

    # best-effort: mark bank txn reconciled
    try:
        from backend.app.core_gov.bank import service as bsvc  # type: ignore
        bsvc.patch(bank_txn_id, {"status": "reconciled", "meta": {"reconcile": {"link_id": rec["id"], "target_type": target_type, "target_id": target_id}}})
    except Exception:
        pass

    return rec


def list_links(bank_txn_id: str = "") -> List[Dict[str, Any]]:
    items = store.list_links()
    if bank_txn_id:
        items = [x for x in items if x.get("bank_txn_id") == bank_txn_id]
    items.sort(key=lambda x: x.get("created_at",""), reverse=True)
    return items[:300]
