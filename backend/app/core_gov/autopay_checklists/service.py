from __future__ import annotations
from typing import Any, Dict, List

def build_for_obligation(obligation_id: str) -> Dict[str, Any]:
    if not (obligation_id or "").strip():
        raise ValueError("obligation_id required")

    # Pull obligation if available
    ob = {}
    try:
        from backend.app.core_gov.budget_obligations import service as obsvc  # type: ignore
        ob = obsvc.get_one(obligation_id) or {}
    except Exception:
        pass

    name = ob.get("name") or obligation_id
    steps = [
        {"step": 1, "title": "Confirm payee details", "done": False, "notes": "Name + account number/reference."},
        {"step": 2, "title": "Choose payment method", "done": False, "notes": "Bank autopay, e-transfer, credit card, PAD."},
        {"step": 3, "title": "Set schedule", "done": False, "notes": "Match due date; set 2–3 days early buffer if possible."},
        {"step": 4, "title": "Confirm notifications", "done": False, "notes": "Enable bank alerts for payment sent/failed."},
        {"step": 5, "title": "Record proof", "done": False, "notes": "Screenshot/reference # stored in Bill Payments proof or Docs."},
    ]
    return {"obligation_id": obligation_id, "name": name, "steps": steps}
