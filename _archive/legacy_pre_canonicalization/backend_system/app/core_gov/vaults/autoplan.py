from __future__ import annotations

from typing import Any, Dict, List


def build_obligation_vault_plan(monthly_buffer_pct: float = 0.10) -> Dict[str, Any]:
    """
    Reads obligations (budget) and suggests:
      - recommended vault name per obligation
      - monthly target funding (amount_due + buffer)
    Does NOT create vaults automatically (safe).
    """
    warnings: List[str] = []
    obligations = []

    try:
        from backend.app.core_gov.budget import service as bsvc  # type: ignore
        obligations = bsvc.list_obligations(status="active")
    except Exception as e:
        warnings.append(f"budget unavailable: {type(e).__name__}: {e}")
        obligations = []

    plan = []
    for ob in obligations:
        name = (ob.get("name") or ob.get("title") or "Obligation").strip()
        amt = float(ob.get("amount") or ob.get("amount_due") or 0.0)
        freq = (ob.get("frequency") or "monthly").strip().lower()
        # normalize to monthly estimate (simple)
        if freq in ("weekly",):
            monthly = amt * 4.33
        elif freq in ("biweekly",):
            monthly = amt * 2.165
        elif freq in ("quarterly",):
            monthly = amt / 3.0
        elif freq in ("yearly", "annual",):
            monthly = amt / 12.0
        else:
            monthly = amt

        buffer = monthly * float(monthly_buffer_pct or 0.10)
        plan.append({
            "obligation_id": ob.get("id",""),
            "obligation_name": name,
            "frequency": freq,
            "base_monthly_est": float(monthly),
            "buffer_monthly_est": float(buffer),
            "monthly_fund_target": float(monthly + buffer),
            "recommended_vault_name": f"{name} Buffer",
            "recommended_category": "bills",
        })

    plan.sort(key=lambda x: float(x.get("monthly_fund_target") or 0.0), reverse=True)
    return {"monthly_buffer_pct": float(monthly_buffer_pct or 0.10), "items": plan, "warnings": warnings}


def create_missing_vaults(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Best-effort helper: creates vaults that don't exist yet.
    """
    warnings: List[str] = []
    created = 0
    skipped = 0
    out_items = []

    try:
        from backend.app.core_gov.vaults import service as vsvc  # type: ignore
        existing = vsvc.list_items()
        existing_names = set((x.get("name") or "").strip().lower() for x in existing)
    except Exception as e:
        return {"created": 0, "skipped": 0, "warnings": [f"vaults unavailable: {type(e).__name__}: {e}"], "items": []}

    for it in (plan or {}).get("items", []):
        vname = (it.get("recommended_vault_name") or "").strip()
        if not vname:
            skipped += 1
            continue
        if vname.lower() in existing_names:
            skipped += 1
            continue
        try:
            v = vsvc.create(name=vname, target=float(it.get("monthly_fund_target") or 0.0), balance=0.0, category=it.get("recommended_category") or "bills", notes="Auto-created from obligation autoplan")
            created += 1
            existing_names.add(vname.lower())
            out_items.append(v)
        except Exception as e:
            warnings.append(f"create vault failed for {vname}: {type(e).__name__}: {e}")

    return {"created": created, "skipped": skipped, "warnings": warnings, "items": out_items}
