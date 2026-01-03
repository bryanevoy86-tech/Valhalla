from __future__ import annotations

from typing import Any, Dict, List, Optional


def _parse_ym(ym: str) -> tuple:
    parts = (ym or "").split("-")
    if len(parts) != 2:
        raise ValueError("month must be YYYY-MM")
    y = int(parts[0]); m = int(parts[1])
    if m < 1 or m > 12:
        raise ValueError("month must be YYYY-MM")
    return y, m


def _in_month(dt: str, y: int, m: int) -> bool:
    try:
        yy, mm, _ = dt.split("-")
        return int(yy) == y and int(mm) == m
    except Exception:
        return False


def month_actuals(month: str) -> Dict[str, Any]:
    y, m = _parse_ym(month)
    warnings: List[str] = []

    # Payments (from obligations module if available)
    pay_total = 0.0
    pay_in = []
    try:
        from backend.app.core_gov.obligations import service as osvc  # type: ignore
        # Attempt to get completed payments if method exists
        payments = []
        if hasattr(osvc, 'list_items'):
            all_oblig = osvc.list_items()
            # Filter by paid status and month
            pay_in = [p for p in all_oblig if _in_month(p.get("paid_date",""), y, m) and p.get("status") == "paid"]
            pay_total = sum(float(p.get("amount") or 0.0) for p in pay_in)
    except Exception as e:
        warnings.append(f"obligations unavailable: {type(e).__name__}: {e}")

    # Receipts (variable spend)
    receipts = []
    try:
        from backend.app.core_gov.receipts import service as rsvc  # type: ignore
        receipts = rsvc.list_items()  # already capped
    except Exception as e:
        warnings.append(f"receipts unavailable: {type(e).__name__}: {e}")
        receipts = []

    rc_in = [r for r in receipts if _in_month(r.get("date",""), y, m)]
    rc_total = sum(float(r.get("total") or 0.0) for r in rc_in)

    # Category rollups (from receipts)
    cat_totals: Dict[str, float] = {}
    for r in rc_in:
        cat = (r.get("category") or "uncategorized").strip() or "uncategorized"
        cat_totals[cat] = cat_totals.get(cat, 0.0) + float(r.get("total") or 0.0)

    # Return summary
    return {
        "month": f"{y:04d}-{m:02d}",
        "payments_total": float(pay_total),
        "receipts_total": float(rc_total),
        "grand_total": float(pay_total + rc_total),
        "receipt_category_totals": {k: float(v) for k, v in sorted(cat_totals.items(), key=lambda kv: -kv[1])},
        "payments_count": len(pay_in),
        "receipts_count": len(rc_in),
        "warnings": warnings,
    }
