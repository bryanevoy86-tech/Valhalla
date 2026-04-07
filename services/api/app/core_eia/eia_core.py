from datetime import datetime
from typing import Any, Dict, List

ALLOWED_EXPENSE_CATEGORIES = {
    "software",
    "hosting",
    "phone",
    "internet",
    "office_supplies",
    "advertising",
    "transport",
    "professional_fees",
    "equipment",
    "other_business",
}

def validate_transaction(tx: Dict[str, Any]) -> Dict[str, Any]:
    required = ["amount", "type", "category"]
    missing = [k for k in required if k not in tx]
    valid = len(missing) == 0
    return {
        "valid": valid,
        "missing_fields": missing,
        "timestamp": datetime.utcnow().isoformat(),
    }

def compliance_check(payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = payload or {}
    missing_receipts = bool(payload.get("missing_receipts", False))
    unclassified_income = bool(payload.get("unclassified_income", False))
    owner_draw = bool(payload.get("owner_draw", False))

    risk = "LOW"
    if missing_receipts or unclassified_income:
        risk = "MEDIUM"
    if owner_draw and payload.get("pre_approval_mode", True):
        risk = "HIGH"

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "missing_receipts": missing_receipts,
        "unclassified_income": unclassified_income,
        "owner_draw": owner_draw,
        "risk": risk,
        "compliant": risk in ("LOW", "MEDIUM"),
    }

def generate_monthly_report(month: str = None) -> Dict[str, Any]:
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "month": month or datetime.utcnow().strftime("%Y-%m"),
        "status": "EIA_REPORT_READY",
        "sections": [
            "income_summary",
            "expense_summary",
            "receipt_index",
            "bank_checklist",
            "declaration_notes",
        ],
    }

def deductible_expense_total(items: List[Dict[str, Any]]) -> float:
    total = 0.0
    for item in items:
        cat = item.get("category")
        amt = float(item.get("amount", 0) or 0)
        if cat in ALLOWED_EXPENSE_CATEGORIES:
            total += amt
    return round(total, 2)
