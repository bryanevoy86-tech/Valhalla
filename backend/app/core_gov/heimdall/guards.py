from __future__ import annotations
from typing import Any, Dict, Tuple

SAFE_ACTIONS = {
    "shopping.generate_from_inventory",
    "shopping.generate_from_needs",
    "shopping.push_reminders",
    "bills.push_reminders",
    "schedule.push_reminders",
    "budget.impact",
    "personal_board.get",
    "cashflow.get",
    "subscriptions.audit",
    "payments.schedule",
    "payments.reconcile",
    "payments.push_reminders",
    "shield.auto_check",
    "shield.state",
}

EXEC_ACTIONS = {
    "bills.paid",
    "shopping.bought",
    "receipts.create",
    "pay_confirm.create",
    "payments.autopay_verified",
}

def guard(mode: str, action: str) -> Tuple[bool, str]:
    mode = (mode or "explore").lower()
    action = (action or "").strip()

    if not action:
        return False, "action required"

    if mode == "explore":
        if action in SAFE_ACTIONS:
            return True, "ok"
        return False, "explore mode allows read/plan actions only"

    if mode == "execute":
        if action in SAFE_ACTIONS or action in EXEC_ACTIONS:
            return True, "ok"
        return False, "unknown or disallowed execute action"

    return False, "invalid mode"
