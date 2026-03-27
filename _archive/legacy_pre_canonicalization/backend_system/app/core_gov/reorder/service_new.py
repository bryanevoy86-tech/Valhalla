from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List


def scan_and_create(desired_by_days: int = 3, dry_run: bool = True) -> Dict[str, Any]:
    """
    If inventory.qty <= reorder_point -> create:
      - shopping item (if shopping module exists)
      - reminder (if reminders module exists)
    """
    warnings: List[str] = []
    created_shopping = 0
    created_reminders = 0
    low_items: List[Dict[str, Any]] = []

    # load inventory
    try:
        from backend.app.core_gov.inventory import service as inv  # type: ignore
        items = inv.list_items(status="active")
    except Exception as e:
        return {"warnings": [f"inventory unavailable: {type(e).__name__}: {e}"], "low_items": [], "created_shopping": 0, "created_reminders": 0}

    for it in items:
        qty = float(it.get("qty") or 0.0)
        rp = float(it.get("reorder_point") or 0.0)
        if rp <= 0:
            continue
        if qty <= rp:
            low_items.append(it)

    # optional: pricebook lookup
    price_by_name = {}
    try:
        from backend.app.core_gov.pricebook import service as pb  # type: ignore
        for p in pb.list_items(status="active"):
            price_by_name[(p.get("item_name") or "").strip().lower()] = p
    except Exception as e:
        warnings.append(f"pricebook unavailable: {type(e).__name__}: {e}")

    desired_by = (date.today() + timedelta(days=int(desired_by_days or 3))).isoformat()

    # create artifacts
    for it in low_items:
        name = (it.get("name") or "").strip()
        desired = float(it.get("desired_qty") or 0.0)
        qty = float(it.get("qty") or 0.0)
        need = max(0.0, desired - qty) if desired > 0 else 1.0

        pb = price_by_name.get(name.lower(), {})
        est_unit = float(pb.get("typical_unit_price") or 0.0)
        preferred_store = pb.get("preferred_store") or ""

        if not dry_run:
            # shopping
            try:
                from backend.app.core_gov.shopping import service as ssvc  # type: ignore
                ssvc.create({
                    "name": name,
                    "qty": float(need),
                    "unit": it.get("unit") or "each",
                    "category": it.get("category") or "general",
                    "priority": "high",
                    "status": "open",
                    "desired_by": desired_by,
                    "est_unit_cost": est_unit,
                    "store_hint": preferred_store,
                    "notes": f"Auto-created by reorder scan from inventory item {it.get('id')}",
                    "meta": {"inventory_item_id": it.get("id","")},
                })
                created_shopping += 1
            except Exception as e:
                warnings.append(f"shopping create failed: {type(e).__name__}: {e}")

            # reminders
            try:
                from backend.app.core_gov.reminders import service as rsvc  # type: ignore
                rsvc.create({
                    "title": f"Reorder: {name}",
                    "due_date": desired_by,
                    "status": "active",
                    "tags": ["reorder", f"inv:{it.get('id','')}"],
                    "notes": "Created by reorder scan. Check shopping list.",
                    "meta": {"inventory_item_id": it.get("id","")},
                })
                created_reminders += 1
            except Exception as e:
                warnings.append(f"reminder create failed: {type(e).__name__}: {e}")

    return {
        "dry_run": bool(dry_run),
        "desired_by": desired_by,
        "low_count": len(low_items),
        "low_items": low_items[:50],
        "created_shopping": created_shopping,
        "created_reminders": created_reminders,
        "warnings": warnings,
    }
