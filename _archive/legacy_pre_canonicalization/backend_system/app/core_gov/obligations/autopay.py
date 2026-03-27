from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, Optional

from . import service as oblig_service


def autopay_guide(obligation_id: str) -> Dict[str, Any]:
    o = oblig_service.get_obligation(obligation_id)
    if not o:
        raise KeyError("obligation not found")

    name = o.get("name") or "Obligation"
    payee = o.get("payee") or "Payee"
    amount = o.get("amount") or 0.0
    due_day = o.get("due_day") or 1

    steps = [
        f"Log into the provider/bank portal for: {payee}.",
        "Find: Payments → Pre-authorized payments (PAD) / Autopay.",
        f"Set payment amount: {amount} (or 'statement balance' where applicable).",
        f"Set withdrawal timing: 3–5 days before due day {due_day}.",
        "Enable email/text confirmation where available.",
        "Take a screenshot / confirmation number and store it in Docs (link it here).",
        "Mark autopay as enabled and then verify after first successful withdrawal.",
    ]

    return {
        "obligation_id": obligation_id,
        "name": name,
        "payee": payee,
        "recommended_withdrawal_day": max(1, int(due_day) - 4),
        "steps": steps,
        "notes": [
            "If provider only allows due-date autopay, schedule a buffer (personal_cash) to prevent NSF.",
            "If the amount varies, use 'minimum due' + manual top-up or 'statement balance' if safe.",
        ],
    }


def set_autopay_enabled(obligation_id: str, enabled: bool = True) -> Dict[str, Any]:
    current = oblig_service.get_obligation(obligation_id)
    if not current:
        raise KeyError("obligation not found")
    
    # Update autopay.enabled in the patch
    patch = {}
    if "autopay" in current:
        autopay_config = current.get("autopay", {})
        autopay_config["enabled"] = bool(enabled)
        patch["autopay"] = autopay_config
    else:
        # Fallback to direct field if old schema
        patch["autopay_enabled"] = bool(enabled)
    
    return oblig_service.patch_obligation(obligation_id, patch)


def set_autopay_verified(obligation_id: str, verified: bool = True, confirmation_ref: str = "") -> Dict[str, Any]:
    current = oblig_service.get_obligation(obligation_id)
    if not current:
        raise KeyError("obligation not found")
    
    patch = {}
    if "autopay" in current:
        autopay_config = current.get("autopay", {})
        autopay_config["verified"] = bool(verified)
        if confirmation_ref:
            autopay_config["reference"] = confirmation_ref
        patch["autopay"] = autopay_config
    else:
        # Fallback to direct fields if old schema
        patch["autopay_verified"] = bool(verified)
        if confirmation_ref:
            patch["meta"] = {"confirmation_ref": confirmation_ref}
    
    return oblig_service.patch_obligation(obligation_id, patch)


def create_verification_followup(obligation_id: str, days_out: int = 7) -> bool:
    o = oblig_service.get_obligation(obligation_id)
    if not o:
        raise KeyError("obligation not found")

    try:
        from backend.app.deals import followups_store  # type: ignore
        followups_store.create_followup({
            "title": f"Verify autopay: {o.get('name')}",
            "due_date": (date.today() + timedelta(days=int(days_out))).isoformat(),
            "priority": "A",
            "status": "open",
            "meta": {"obligation_id": obligation_id, "payee": o.get("payee") or ""},
        })
        return True
    except Exception:
        return False
