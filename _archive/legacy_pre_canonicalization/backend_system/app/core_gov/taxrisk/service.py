from __future__ import annotations

from typing import Any, Dict, List, Tuple


SAFE_CATS = {"utilities", "insurance", "office", "software", "marketing", "supplies", "tools", "repairs", "training"}
AGG_CATS = {"meals", "travel", "clothing", "home", "entertainment"}
SAFE_TAGS = {"business", "worksite", "client", "invoice", "materials"}
AGG_TAGS = {"personal", "family", "gift", "luxury", "vacation"}


def assess(category: str = "", tags: List[str] = None, vendor: str = "", notes: str = "") -> Dict[str, Any]:
    tags = tags or []
    cat = (category or "").strip().lower()
    tset = {str(t).strip().lower() for t in tags if str(t).strip()}

    score = 0.0
    reasons: List[str] = []

    if cat in SAFE_CATS:
        score += 0.2
        reasons.append("category_safe")
    if cat in AGG_CATS:
        score += 0.7
        reasons.append("category_often_audited")

    if tset & SAFE_TAGS:
        score -= 0.2
        reasons.append("tags_support_business_use")
    if tset & AGG_TAGS:
        score += 0.3
        reasons.append("tags_suggest_personal_use")

    # bound 0..1
    if score < 0.0:
        score = 0.0
    if score > 1.0:
        score = 1.0

    if score <= 0.35:
        risk = "safe"
    elif score <= 0.65:
        risk = "medium"
    else:
        risk = "aggressive"

    return {"risk": risk, "score": float(score), "reasons": reasons, "meta": {"category": cat, "tags": sorted(list(tset))}}
