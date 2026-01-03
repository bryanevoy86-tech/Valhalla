from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ym_from_date(ds: str) -> str:
    try:
        y, m, _ = ds.split("-")
        return f"{int(y):04d}-{int(m):02d}"
    except Exception:
        return "unknown"


def build(year: int, currency: str = "CAD") -> Dict[str, Any]:
    year = int(year or 0)
    if year < 2000 or year > 2100:
        raise ValueError("year must be a reasonable YYYY")

    warnings: List[str] = []

    # receipts
    receipts = []
    try:
        from backend.app.core_gov.receipts import service as rsvc  # type: ignore
        receipts = rsvc.list_items()
    except Exception as e:
        warnings.append(f"receipts unavailable: {type(e).__name__}: {e}")
        receipts = []

    rc_in = []
    for r in receipts:
        try:
            y = int((r.get("date","") or "").split("-")[0])
        except Exception:
            continue
        if y == year:
            rc_in.append(r)

    # payments
    pays = []
    try:
        from backend.app.core_gov.budget import store as bstore  # type: ignore
        pays = bstore.list_payments()
    except Exception as e:
        warnings.append(f"payments unavailable: {type(e).__name__}: {e}")
        pays = []

    pay_in = []
    for p in pays:
        try:
            y = int((p.get("paid_date","") or "").split("-")[0])
        except Exception:
            continue
        if y == year:
            pay_in.append(p)

    # month rollup
    month_totals: Dict[str, float] = {}
    for r in rc_in:
        ym = _ym_from_date(r.get("date",""))
        month_totals[ym] = month_totals.get(ym, 0.0) + float(r.get("total") or 0.0)
    for p in pay_in:
        ym = _ym_from_date(p.get("paid_date",""))
        month_totals[ym] = month_totals.get(ym, 0.0) + float(p.get("amount") or 0.0)

    # receipt category rollup
    cat_totals: Dict[str, float] = {}
    for r in rc_in:
        cat = (r.get("category") or "uncategorized").strip() or "uncategorized"
        cat_totals[cat] = cat_totals.get(cat, 0.0) + float(r.get("total") or 0.0)

    # risk rollup (best-effort)
    risk_totals = {"safe": 0.0, "medium": 0.0, "aggressive": 0.0, "unknown": 0.0}
    try:
        from backend.app.core_gov.taxrisk import service as trs  # type: ignore
        for r in rc_in:
            cat = (r.get("category") or "").strip()
            tags = r.get("tags") or []
            out = trs.assess(category=cat, tags=tags, vendor=r.get("vendor",""), notes=r.get("notes",""))
            risk = out.get("risk") or "unknown"
            risk_totals[risk] = float(risk_totals.get(risk, 0.0) + float(r.get("total") or 0.0))
    except Exception as e:
        warnings.append(f"taxrisk unavailable: {type(e).__name__}: {e}")
        risk_totals["unknown"] = float(sum(float(r.get("total") or 0.0) for r in rc_in))

    export = {
        "year": year,
        "currency": currency,
        "generated_at": _utcnow_iso(),
        "totals": {
            "receipts_total": float(sum(float(r.get("total") or 0.0) for r in rc_in)),
            "payments_total": float(sum(float(p.get("amount") or 0.0) for p in pay_in)),
            "grand_total": float(sum(month_totals.values())),
        },
        "by_month": {k: float(v) for k, v in sorted(month_totals.items())},
        "receipt_by_category": {k: float(v) for k, v in sorted(cat_totals.items(), key=lambda kv: -kv[1])},
        "receipt_by_risk": {k: float(v) for k, v in risk_totals.items()},
        "counts": {"receipts": len(rc_in), "payments": len(pay_in)},
        "warnings": warnings,
        "note": "Export is informational and audit-ready structure. Improve by categorizing receipts and adding tags.",
    }

    rec = {"id": "ye_" + uuid.uuid4().hex[:12], "created_at": _utcnow_iso(), "export": export}
    items = store.list_items()
    items.append(rec)
    if len(items) > 60:
        items = items[-60:]
    store.save_items(items)
    return rec


def list_items(limit: int = 10) -> List[Dict[str, Any]]:
    items = store.list_items()
    items.sort(key=lambda x: x.get("created_at",""), reverse=True)
    return items[: int(limit or 10)]
