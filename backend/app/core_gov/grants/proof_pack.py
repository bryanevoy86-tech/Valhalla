from __future__ import annotations

from typing import Any

DEFAULT_DOCS = [
    "Business registration (corporation/sole prop documents)",
    "Proof of address + ID for signing authority",
    "Business plan / project summary (1–3 pages)",
    "Budget + use-of-funds breakdown",
    "Quotes/estimates (if equipment/services)",
    "Financials (bank statements or projections)",
    "Tax accounts (CRA program accounts if applicable)",
    "Team/roles + resumes (if hiring/training grant)",
]

CATEGORY_DOCS = {
    "hiring": [
        "Job descriptions",
        "Hiring plan + wage estimate",
        "Training plan (if applicable)",
    ],
    "green": [
        "Energy/emissions rationale",
        "Equipment specs + vendor quote",
    ],
    "innovation": [
        "Problem/solution brief",
        "Milestones + timeline",
        "IP/tech summary (if any)",
    ],
    "export": [
        "Target markets + go-to-market plan",
        "Marketing budget + timeline",
    ],
    "training": [
        "Training provider quote",
        "Training objectives + outcomes",
    ],
}


def build_proof_pack(grant: dict[str, Any]) -> dict[str, Any]:
    category = (grant.get("category") or "general").lower()
    docs = list(DEFAULT_DOCS)

    docs.extend(CATEGORY_DOCS.get(category, []))

    # include any explicit docs already stored
    explicit = grant.get("required_docs") or []
    for d in explicit:
        if d not in docs:
            docs.append(d)

    return {
        "grant_id": grant.get("id"),
        "category": category,
        "deadline_utc": grant.get("deadline_utc"),
        "recommended_documents": docs,
        "notes": [
            "This is a checklist pack to speed up applications.",
            "Exact requirements vary by grant—confirm on the official page.",
        ],
    }
