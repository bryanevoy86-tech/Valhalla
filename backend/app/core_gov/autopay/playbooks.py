from __future__ import annotations
from typing import Any, Dict, List

DEFAULT_STEPS = [
    "Confirm the payee name matches the official statement exactly (no abbreviations).",
    "Confirm the amount & cadence (monthly/quarterly) and whether it can vary.",
    "Confirm withdrawal account number and that it is dedicated for bills if possible.",
    "Set a calendar reminder 2 days before first draft to verify balance.",
    "Keep the first confirmation email/screenshot in Document Vault (later automation).",
    "After first successful draft, mark as autopay_verified.",
]

CANADA_STEPS = [
    "If using PAD (pre-authorized debit), confirm vendor has your correct transit/institution/account.",
    "If using e-Transfer for recurring, confirm whether scheduling is supported and any limits.",
    "If using credit-card autopay, confirm card expiry alerts are enabled.",
]

def playbook(country: str = "CA") -> Dict[str, Any]:
    c = (country or "CA").upper()
    steps = list(DEFAULT_STEPS)
    if c in ("CA", "CAN", "CANADA"):
        steps += CANADA_STEPS
    return {"country": c, "steps": steps}
