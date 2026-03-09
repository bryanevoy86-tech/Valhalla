from __future__ import annotations

from typing import Any, Dict, List

def _resolve_vault_id(vault_id: str, vault_name: str) -> str:
    if vault_id:
        return vault_id
    if not vault_name:
        return ""
    try:
        from backend.app.core_gov.vaults import service as vsvc  # type: ignore
        for v in vsvc.list_items():
            if (v.get("name","").lower() == vault_name.lower()):
                return v.get("id","")
    except Exception:
        return ""
    return ""

def preview(rule_id: str, amount: float) -> Dict[str, Any]:
    warnings: List[str] = []
    try:
        from backend.app.core_gov.allocation_rules import store as arstore  # type: ignore
        rules = arstore.list_items()
        rule = next((r for r in rules if r.get("id") == rule_id), None)
    except Exception as e:
        return {"items": [], "warnings": [f"allocation_rules unavailable: {type(e).__name__}: {e}"]}

    if not rule:
        return {"items": [], "warnings": ["rule not found"]}

    amt = float(amount or 0.0)
    items = []
    used = 0.0
    for s in (rule.get("splits") or []):
        pct = float(s.get("pct") or 0.0)
        alloc = round(amt * (pct / 100.0), 2)
        used += alloc
        vid = _resolve_vault_id(s.get("vault_id",""), s.get("vault_name",""))
        if not vid:
            warnings.append(f"vault not resolved for split: {s}")
        items.append({"vault_id": vid, "vault_name": s.get("vault_name",""), "pct": pct, "amount": alloc})

    leftover = round(amt - used, 2)
    return {"rule_id": rule_id, "amount": amt, "allocations": items, "leftover": leftover, "warnings": warnings}

def apply(rule_id: str, amount: float, date: str, income_description: str = "Payday", account_id: str = "") -> Dict[str, Any]:
    res = preview(rule_id=rule_id, amount=amount)
    warnings = res.get("warnings") or []

    # record income in ledger
    try:
        from backend.app.core_gov.ledger import service as lsvc  # type: ignore
        lsvc.create(kind="income", date=date, amount=float(amount or 0.0), description=income_description, account_id=account_id)
    except Exception as e:
        warnings.append(f"ledger unavailable: {type(e).__name__}: {e}")

    # adjust vault balances + write transfer entries
    applied = 0
    try:
        from backend.app.core_gov.vaults import service as vsvc  # type: ignore
        from backend.app.core_gov.ledger import service as lsvc  # type: ignore
        for a in res.get("allocations") or []:
            vid = a.get("vault_id","")
            if not vid:
                continue
            amt = float(a.get("amount") or 0.0)
            if amt <= 0:
                continue
            vsvc.adjust(vault_id=vid, delta=amt, reason=f"Allocation {rule_id}")
            lsvc.create(kind="transfer", date=date, amount=amt, description=f"Allocate to vault {vid}", category="allocation", account_id=account_id, meta={"vault_id": vid, "rule_id": rule_id})
            applied += 1
    except Exception as e:
        warnings.append(f"vaults/ledger apply failed: {type(e).__name__}: {e}")

    return {"rule_id": rule_id, "amount": float(amount or 0.0), "date": date, "applied_splits": applied, "leftover": res.get("leftover", 0.0), "warnings": warnings, "preview": res}
