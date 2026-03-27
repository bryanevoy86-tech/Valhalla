from __future__ import annotations

from typing import Any

BASE = [
    "Government ID + proof of address",
    "Business registration docs",
    "Business bank statements (if available)",
    "Basic P&L or income proof (even simple)",
    "Use-of-funds statement (what you will spend on)",
    "Vendor quotes (equipment/marketing/services)",
    "Credit report snapshot (if required)",
    "References (if credit union/private)",
]

TYPE_ADDONS = {
    "equipment": ["Equipment details + serial/specs quote", "Insurance plan (if required)"],
    "loc": ["Cash flow summary + monthly expenses", "Debt schedule (if any)"],
    "vendor": ["Vendor account application details", "Trade references (if requested)"],
    "sba": ["Residency/eligibility proof", "Business history/operating agreement"],
}


def build_underwriting_checklist(loan: dict[str, Any]) -> dict[str, Any]:
    ptype = (loan.get("product_type") or "microloan").lower()
    docs = list(BASE)
    docs.extend(TYPE_ADDONS.get(ptype, []))

    explicit = loan.get("required_docs") or []
    for d in explicit:
        if d not in docs:
            docs.append(d)

    return {
        "loan_id": loan.get("id"),
        "product_type": ptype,
        "recommended_documents": docs,
        "risk_notes": [
            "If you lack credit/revenue history, focus on microloan/credit union/vendor tiers first.",
            "Always keep use-of-funds tight and verifiable.",
        ],
    }
