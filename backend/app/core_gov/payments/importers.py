from __future__ import annotations
from typing import Any, Dict, List
from . import store

def import_all() -> Dict[str, Any]:
    created = 0
    warnings: List[str] = []
    existing = store.list_items()
    existing_names = {(x.get("name","").lower(), x.get("kind","")) for x in existing}

    # Bills
    try:
        from backend.app.core_gov.bills import store as bstore  # type: ignore
        if hasattr(bstore, "list_bills"):
            bills = bstore.list_bills()
        else:
            bills = []
            warnings.append("bills.list_bills not found")
        for b in bills[:5000]:
            key = ((b.get("name") or "").lower(), "bill")
            if key in existing_names:
                continue
            store.create(
                name=b.get("name") or "Bill",
                amount=float(b.get("amount") or 0.0),
                cadence=str(b.get("cadence") or "monthly"),
                currency=str(b.get("currency") or "CAD"),
                due_day=int(b.get("due_day") or 1),
                kind="bill",
                payee=str(b.get("payee") or ""),
                autopay_enabled=bool(b.get("autopay_enabled") or False),
                autopay_verified=bool(b.get("autopay_verified") or False),
                notes="imported from bills"
            )
            created += 1
    except Exception as e:
        warnings.append(f"bills import failed: {type(e).__name__}: {e}")

    # Subs
    try:
        from backend.app.core_gov.subscriptions import store as sstore  # type: ignore
        subs = sstore.list_items()
        for s in subs[:5000]:
            key = ((s.get("name") or "").lower(), "subscription")
            if key in existing_names:
                continue
            store.create(
                name=s.get("name") or "Subscription",
                amount=float(s.get("amount") or 0.0),
                cadence=str(s.get("cadence") or "monthly"),
                currency=str(s.get("currency") or "CAD"),
                due_day=int(s.get("renewal_day") or 1),
                kind="subscription",
                payee="",
                autopay_enabled=False,
                autopay_verified=False,
                notes="imported from subscriptions"
            )
            created += 1
    except Exception as e:
        warnings.append(f"subscriptions import failed: {type(e).__name__}: {e}")

    return {"created": created, "warnings": warnings}
