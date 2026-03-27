from __future__ import annotations
from typing import Any, Dict

def dispatch(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    action = (action or "").strip()
    payload = payload or {}

    # SHOPPING
    if action == "shopping.generate_from_inventory":
        try:
            from backend.app.core_gov.shopping.from_inventory import generate  # type: ignore
            return generate(limit=int(payload.get("limit") or 50))
        except Exception as e:
            return {"ok": False, "error": f"failed: {type(e).__name__}"}
    
    if action == "shopping.generate_from_needs":
        try:
            from backend.app.core_gov.shopping.from_schedule_needs import generate  # type: ignore
            return generate(within_days=int(payload.get("within_days") or 30), limit=int(payload.get("limit") or 50))
        except Exception as e:
            return {"ok": False, "error": f"failed: {type(e).__name__}"}
    
    if action == "shopping.push_reminders":
        try:
            from backend.app.core_gov.shopping.reminders import push  # type: ignore
            return push()
        except Exception as e:
            return {"ok": False, "error": f"failed: {type(e).__name__}"}

    # BILLS
    if action == "bills.push_reminders":
        try:
            from backend.app.core_gov.bills.reminders import push  # type: ignore
            return push(days_ahead=int(payload.get("days_ahead") or 7))
        except Exception as e:
            return {"ok": False, "error": f"failed: {type(e).__name__}"}

    # SCHEDULE
    if action == "schedule.push_reminders":
        try:
            from backend.app.core_gov.schedule.reminders import push  # type: ignore
            return push(days_ahead=int(payload.get("days_ahead") or 1))
        except Exception as e:
            return {"ok": False, "error": f"failed: {type(e).__name__}"}

    # BUDGET
    if action == "budget.impact":
        try:
            from backend.app.core_gov.budget.impact import impact  # type: ignore
            return impact(buffer_min=float(payload.get("buffer_min") or 500.0))
        except Exception as e:
            return {"ok": False, "error": f"failed: {type(e).__name__}"}

    # PERSONAL BOARD
    if action == "personal_board.get":
        try:
            from backend.app.core_gov.personal_board.service import board  # type: ignore
            return board()
        except Exception as e:
            return {"ok": False, "error": f"failed: {type(e).__name__}"}

    # CASHFLOW
    if action == "cashflow.get":
        try:
            from backend.app.core_gov.cashflow.service import forecast  # type: ignore
            return forecast(days=int(payload.get("days") or 30))
        except Exception as e:
            return {"ok": False, "error": f"failed: {type(e).__name__}"}

    # SUBSCRIPTIONS
    if action == "subscriptions.audit":
        try:
            from backend.app.core_gov.subscriptions.audit import audit  # type: ignore
            return audit()
        except Exception as e:
            return {"ok": False, "error": f"failed: {type(e).__name__}"}

    # PAYMENTS
    if action == "payments.schedule":
        try:
            from backend.app.core_gov.payments import store as pstore  # type: ignore
            from backend.app.core_gov.payments.service import schedule as sched  # type: ignore
            return {"items": sched(pstore.list_items(), days=int(payload.get("days") or 30))}
        except Exception as e:
            return {"ok": False, "error": f"failed: {type(e).__name__}"}

    if action == "payments.reconcile":
        try:
            from backend.app.core_gov.reconcile.service import reconcile  # type: ignore
            return reconcile(days=int(payload.get("days") or 30))
        except Exception as e:
            return {"ok": False, "error": f"failed: {type(e).__name__}"}

    if action == "payments.push_reminders":
        try:
            from backend.app.core_gov.payments.reminders import push  # type: ignore
            return push(days_ahead=int(payload.get("days_ahead") or 5))
        except Exception as e:
            return {"ok": False, "error": f"failed: {type(e).__name__}"}

    if action == "shield.auto_check":
        try:
            from backend.app.core_gov.shield_lite.auto import check_and_trigger  # type: ignore
            return check_and_trigger(buffer_min=float(payload.get("buffer_min") or 500.0))
        except Exception as e:
            return {"ok": False, "error": f"failed: {type(e).__name__}"}

    if action == "shield.state":
        try:
            from backend.app.core_gov.shield_lite import store as sstore  # type: ignore
            return sstore.get_state()
        except Exception as e:
            return {"ok": False, "error": f"failed: {type(e).__name__}"}

    if action == "pay_confirm.create":
        try:
            from backend.app.core_gov.pay_confirm import store as cstore  # type: ignore
            return cstore.create(
                payment_id=str(payload.get("payment_id") or ""),
                paid_on=str(payload.get("paid_on") or ""),
                amount=float(payload.get("amount") or 0.0),
                currency=str(payload.get("currency") or "CAD"),
                method=str(payload.get("method") or ""),
                ref=str(payload.get("ref") or ""),
                notes=str(payload.get("notes") or ""),
            )
        except Exception as e:
            return {"ok": False, "error": f"failed: {type(e).__name__}"}

    if action == "payments.autopay_verified":
        try:
            from backend.app.core_gov.payments.autopay_verify import mark_verified  # type: ignore
            return mark_verified(
                payment_id=str(payload.get("payment_id") or ""),
                verified=bool(payload.get("verified") if "verified" in payload else True),
                proof_note=str(payload.get("proof_note") or ""),
            )
        except Exception as e:
            return {"ok": False, "error": f"failed: {type(e).__name__}"}

    return {"ok": False, "error": "unknown action"}
