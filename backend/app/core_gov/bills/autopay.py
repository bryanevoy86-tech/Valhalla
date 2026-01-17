from __future__ import annotations
from typing import Any, Dict, List

def checklist(bill: Dict[str, Any]) -> Dict[str, Any]:
    name = bill.get("name","")
    payee = bill.get("payee","")
    steps = [
        f"Log into your bank app/online banking for the account you use to pay {name}.",
        "Find: Payments / Bill Payments / Payees.",
        f"Add payee: {payee or '(enter payee name)'} if not already added.",
        "Set payment amount (fixed or minimum) and frequency.",
        "Set start date and ensure it hits before the due date.",
        "Enable email/SMS notifications for successful payment + failures.",
        "Keep a 1-bill buffer in the account so it never bounces.",
    ]
    return {"bill_id": bill.get("id"), "name": name, "steps": steps}

def checklist_for_all(bills: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"items": [checklist(b) for b in bills if b.get("status") == "active"][:200]}
