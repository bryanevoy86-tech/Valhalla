from __future__ import annotations

from typing import Any, Dict, List

from backend.app.core_gov.budget import service as bsvc


def build_autopay_plan(obligation_id: str, bank: str = "", mode: str = "checklist", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    ob = bsvc.get_obligation(obligation_id)
    if not ob:
        raise KeyError("obligation not found")

    name = ob.get("name","")
    payee = ob.get("payee","")
    amount = float(ob.get("amount") or 0.0)
    cadence = ob.get("cadence") or "monthly"
    due_day = int(ob.get("due_day") or 1)
    method = ob.get("method") or "manual"

    bank_hint = (bank or ob.get("account_hint") or "").strip()

    checklist: List[str] = []
    reminders: List[str] = []

    checklist.append(f"Open your banking app/website{(' (' + bank_hint + ')') if bank_hint else ''}.")
    checklist.append("Go to: Payments / Bills / Payees / Scheduled payments (wording varies by bank).")
    checklist.append(f"Add payee (biller/landlord/provider): '{payee or name}'.")
    checklist.append(f"Set amount: {amount:.2f} {ob.get('currency','CAD')}.")
    checklist.append(f"Set frequency: {cadence}.")
    checklist.append(f"Set next payment date: the next '{due_day}' (or the closest earlier business day if your bank requires).")
    checklist.append("Choose funding account (chequing) and confirm.")
    checklist.append("Turn on notifications: payment scheduled + payment processed + insufficient funds warnings.")
    checklist.append("Save a screenshot/PDF confirmation and store it in /core/docs as proof.")

    if method != "autopay" or not bool(ob.get("autopay_enabled")):
        reminders.append(f"If you keep this manual: create a reminder 3 days before the {due_day}th each cycle.")
        reminders.append("If funds are tight: set a second reminder 1 day before due date to verify balance.")
        reminders.append("If you miss a payment once: switch this obligation to autopay immediately.")

    notes = "This is guidance only. Valhalla does not execute bank transactions in v1."

    return {
        "obligation_id": obligation_id,
        "obligation_name": name,
        "autopay_recommended": True,
        "checklist": checklist if mode in ("checklist","guidance") else [],
        "reminders": reminders,
        "notes": notes,
        "meta": {"bank": bank_hint, **meta},
    }
