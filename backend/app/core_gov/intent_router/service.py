from __future__ import annotations

from typing import Any, Dict, List

def handle_intent(intent: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    i = (intent or "").strip().lower()
    if not i:
        raise ValueError("intent required")

    # household finance
    if i == "add_bill":
        from backend.app.core_gov.budget_obligations import service as obsvc  # type: ignore
        return obsvc.create(
            name=payload.get("name",""),
            amount=float(payload.get("amount") or 0.0),
            cadence=payload.get("cadence","monthly"),
            due_day=int(payload.get("due_day") or 1),
            due_months=int(payload.get("due_months") or 1),
            pay_to=payload.get("pay_to",""),
            category=payload.get("category","household"),
            autopay_status=payload.get("autopay_status","unknown"),
            notes=payload.get("notes",""),
        )

    if i == "add_item":
        from backend.app.core_gov.shopping_list import service as ssvc  # type: ignore
        return ssvc.add(
            item=payload.get("item",""),
            qty=float(payload.get("qty") or 1.0),
            unit=payload.get("unit","each"),
            priority=payload.get("priority","normal"),
            category=payload.get("category","grocery"),
            notes=payload.get("notes",""),
        )

    if i == "add_event":
        from backend.app.core_gov.house_calendar import service as csvc  # type: ignore
        return csvc.create(
            title=payload.get("title",""),
            date=payload.get("date",""),
            time=payload.get("time",""),
            location=payload.get("location",""),
            category=payload.get("category","household"),
            notes=payload.get("notes",""),
        )

    if i == "set_goal":
        from backend.app.core_gov.big_purchases import service as bsvc  # type: ignore
        return bsvc.create(
            title=payload.get("title",""),
            target_amount=float(payload.get("target_amount") or 0.0),
            target_date=payload.get("target_date",""),
            vault_id=payload.get("vault_id",""),
            vault_name=payload.get("vault_name",""),
            priority=payload.get("priority","normal"),
            notes=payload.get("notes",""),
        )

    if i == "daily_guard":
        from backend.app.core_gov.guardrails import service as gsvc  # type: ignore
        return gsvc.daily_guard(days_ahead=int(payload.get("days_ahead") or 7))

    raise ValueError(f"unknown intent: {intent}")
