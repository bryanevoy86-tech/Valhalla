from __future__ import annotations

from typing import Any, Dict, List

def export_bundle(keys: List[str]) -> Dict[str, Any]:
    warnings: List[str] = []
    out: Dict[str, Any] = {"bundle": {}, "warnings": warnings}

    for k in (keys or []):
        try:
            if k == "ledger":
                from backend.app.core_gov.ledger import store as s  # type: ignore
                out["bundle"][k] = s.list_items()
            elif k == "budget_obligations":
                from backend.app.core_gov.budget_obligations import store as s  # type: ignore
                out["bundle"][k] = s.list_items()
            elif k == "bill_payments":
                from backend.app.core_gov.bill_payments import store as s  # type: ignore
                out["bundle"][k] = s.list_items()
            elif k == "vaults":
                from backend.app.core_gov.vaults import store as s  # type: ignore
                out["bundle"][k] = s.list_items()
            elif k == "shopping_list":
                from backend.app.core_gov.shopping_list import store as s  # type: ignore
                out["bundle"][k] = s.list_items()
            elif k == "house_inventory":
                from backend.app.core_gov.house_inventory import store as s  # type: ignore
                out["bundle"][k] = s.list_items()
            else:
                warnings.append(f"unknown key: {k}")
        except Exception as e:
            warnings.append(f"export {k} failed: {type(e).__name__}: {e}")

    return out
