from __future__ import annotations

from typing import Any, Dict, List


def score_buffers(days: int = 30) -> Dict[str, Any]:
    warnings: List[str] = []

    # pull vault funding suggestion
    suggested = {}
    try:
        from backend.app.core_gov.vaults import allocator  # type: ignore
        suggested = allocator.suggest_funding(days=int(days or 30))
        warnings += suggested.get("warnings", [])
    except Exception as e:
        warnings.append(f"vault allocator unavailable: {type(e).__name__}: {e}")
        suggested = {"plan": []}

    # read current vault balances
    vaults = []
    try:
        from backend.app.core_gov.vaults import service as vsvc  # type: ignore
        vaults = vsvc.list_items()
    except Exception as e:
        warnings.append(f"vaults unavailable: {type(e).__name__}: {e}")
        vaults = []

    bal_by_name = { (v.get("name") or "").strip().lower(): float(v.get("balance") or 0.0) for v in vaults }

    rows = []
    overall_score = 0.0
    for p in (suggested.get("plan") or []):
        nm = (p.get("vault_name") or "").strip()
        need = float(p.get("suggested_amount") or 0.0)
        have = float(bal_by_name.get(nm.lower(), 0.0))
        ratio = (have / need) if need > 0 else 1.0

        if ratio >= 1.0:
            grade = "green"
        elif ratio >= 0.65:
            grade = "yellow"
        else:
            grade = "red"

        rows.append({"vault_name": nm, "need": need, "have": have, "coverage_ratio": float(ratio), "grade": grade})
        overall_score += min(1.0, max(0.0, ratio))

    max_score = max(1, len(rows))
    overall = overall_score / max_score

    if overall >= 0.9:
        status = "stable"
    elif overall >= 0.65:
        status = "watch"
    else:
        status = "risk"

    return {"range_days": int(days or 30), "status": status, "overall_score": float(overall), "items": rows, "warnings": warnings}
