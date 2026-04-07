from __future__ import annotations

from typing import Any


def evaluate_financial_risk(intent_data: dict[str, Any]) -> dict[str, Any]:
    amount = float(intent_data.get("amount", 0) or 0)
    purpose = str(intent_data.get("purpose", "") or "")
    payee = str(intent_data.get("payee", "") or "")

    reasons: list[str] = []

    if amount <= 0:
        reasons.append("Amount must be greater than zero")

    if amount > 50000:
        reasons.append("High-value payment requires manual review")

    if not purpose:
        reasons.append("Purpose is missing")

    if not payee:
        reasons.append("Payee is missing")

    blocked = len(reasons) > 0
    return {
        "blocked": blocked,
        "reasons": reasons,
        "risk_level": "high" if blocked else ("medium" if amount > 10000 else "low"),
    }
