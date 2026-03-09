"""
Stub for Heimdall integration. Replace with real LLM/tooling later.
Keep pure functions so it's easy to unit test.
"""

from typing import TypedDict


class UnderwriteInput(TypedDict):
    address: str
    beds: int
    baths: float
    sqft: int
    arv_comps: list[float]
    repair_notes: str


def suggest_arv(data: UnderwriteInput) -> float:
    """
    Naive ARV suggestion: average of comps.
    (Swap for model or external service when ready.)
    """
    comps = data.get("arv_comps") or []
    if not comps:
        return 0.0
    return round(sum(comps) / len(comps), 2)
