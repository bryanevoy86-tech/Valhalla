"""Zone Expansion Engine Service"""
from sqlalchemy.orm import Session

from .schemas import (
    ExpansionCriteriaStatus,
    ZoneExpansionRecommendation,
    ZoneExpansionRequest,
)


def get_expansion_recommendation(
    db: Session, payload: ZoneExpansionRequest
) -> ZoneExpansionRecommendation:
    """
    Get zone expansion recommendation.
    
    Placeholder implementation. Later, this should:
    - Pull zone stats from your real zones table
    - Evaluate BRRRR stability, cashflow, refi cycles, automation coverage
    - Choose best next zone with confidence score
    """

    # TODO: replace with real logic using zones + brrrr_stability
    criteria = ExpansionCriteriaStatus(
        brrrr_stability_met=True,
        cashflow_multiple_met=True,
        refi_cycles_met=True,
        automation_coverage_met=False,
    )

    notes = [
        "Automation coverage is below the 80% target threshold.",
        "BRRRR stability and cashflow multiples are within safe expansion bands.",
        "Refi cycles meet the minimum criteria.",
    ]

    plan = [
        "Increase automation coverage in the current zone above 80%.",
        "Prepare contractor lists and reno patterns for the next zone.",
        "Re-run expansion check in 14 days.",
    ]

    rec = ZoneExpansionRecommendation(
        starting_zone=payload.starting_zone,
        target_zone="NEXT_MARKET_PLACEHOLDER",
        confidence=0.75,
        criteria=criteria,
        notes=notes,
        action_plan=plan,
    )
    return rec
