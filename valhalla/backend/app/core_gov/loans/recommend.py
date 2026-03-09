from __future__ import annotations

from typing import Any


def recommend_next_step(profile: dict[str, Any], loans: list[dict[str, Any]]) -> dict[str, Any]:
    """
    profile fields (suggested):
    - country: CA|US
    - province_state
    - has_credit_history: bool
    - has_revenue_history: bool
    - needs_amount: float
    """
    country = (profile.get("country") or "CA").upper()
    prov = (profile.get("province_state") or "").upper()
    has_credit = bool(profile.get("has_credit_history", False))
    has_rev = bool(profile.get("has_revenue_history", False))
    needs = float(profile.get("needs_amount") or 0)

    candidates = []
    for l in loans:
        if (l.get("country") or "CA").upper() != country:
            continue
        lp = (l.get("province_state") or "").upper()
        if lp and prov and lp != prov:
            continue

        if l.get("requires_credit_history", True) and not has_credit:
            continue
        if l.get("requires_revenue_history", False) and not has_rev:
            continue

        min_amt = l.get("min_amount")
        max_amt = l.get("max_amount")
        if needs and max_amt is not None and needs > float(max_amt):
            continue
        if needs and min_amt is not None and needs < float(min_amt):
            # still possible, but lower fit
            pass

        fit = 70
        if not l.get("requires_credit_history", True):
            fit += 10
        if not l.get("requires_revenue_history", False):
            fit += 5
        if l.get("product_type") in ("microloan", "credit_union", "vendor"):
            fit += 5

        candidates.append((fit, l))

    candidates.sort(key=lambda x: x[0], reverse=True)

    top = [{
        "loan_id": l.get("id"),
        "name": l.get("name"),
        "lender": l.get("lender"),
        "product_type": l.get("product_type"),
        "min_amount": l.get("min_amount"),
        "max_amount": l.get("max_amount"),
        "requires_credit_history": l.get("requires_credit_history"),
        "requires_revenue_history": l.get("requires_revenue_history"),
        "fit_score": fit,
    } for fit, l in candidates[:10]]

    return {
        "profile": {"country": country, "province_state": prov, "has_credit_history": has_credit, "has_revenue_history": has_rev, "needs_amount": needs},
        "recommendations": top,
        "notes": [
            "This is guidance only; verify lender criteria on official pages.",
            "If nothing matches, add more loan entries or adjust profile assumptions.",
        ],
    }
