"""
Research Completion Readiness Service

Checks whether enough research is complete to safely proceed with owner outreach.
"""

from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.heimdall.models.persistence import HeimdallTask
from app.heimdall.services.property_intel_service import (
    get_property_intel_record,
    mark_property_ready_for_outreach,
)


REQUIRED_RESEARCH_FINDINGS = [
    "owner_name",
    "ownership_unverified",
    "estimated_arv",
]

RECOMMENDED_RESEARCH_FINDINGS = [
    "tax_arrears_known",
    "out_of_area_owner",
    "property_condition",
    "vacant_or_occupied",
    "recent_sales_checked",
    "assessment_checked",
]


def evaluate_research_readiness(
    db: Session,
    property_intel_id: str,
) -> Dict[str, Any]:
    """
    Evaluate whether a property has enough research to proceed with owner outreach.

    Checks:
    1. Required findings present (owner_name, ownership status, estimated value)
    2. Ownership verified
    3. Distress score >= 50
    4. Property status not blocked
    5. All research tasks completed

    If all pass: marks property READY_FOR_OUTREACH and returns go-ahead.
    If any fail: returns blockers list for VA to address.

    Args:
        db: SQLAlchemy session
        property_intel_id: Property to evaluate

    Returns:
        {
            "status": "READY_FOR_OUTREACH" | "NOT_READY_FOR_OUTREACH",
            "property_intel_id": str,
            "blockers": [] or [blocker_codes],
            "missing_required": [] or [field_names],
            "missing_recommended": [] or [field_names],
            "distress_score": int,
            "research_status": str,
            "outreach_allowed": bool,
            "next_action": str,
        }
    """

    record = get_property_intel_record(db, property_intel_id)

    if not record:
        return {
            "status": "ERROR",
            "reason": "Property intel record not found.",
        }

    property_data = record.property_data or {}

    # Check required findings
    missing_required = [
        field for field in REQUIRED_RESEARCH_FINDINGS
        if field not in property_data or property_data.get(field) in [None, ""]
    ]

    # Check recommended findings
    missing_recommended = [
        field for field in RECOMMENDED_RESEARCH_FINDINGS
        if field not in property_data or property_data.get(field) in [None, ""]
    ]

    # Check for open tasks
    open_tasks = (
        db.query(HeimdallTask)
        .filter(HeimdallTask.deal_id == property_intel_id)
        .filter(HeimdallTask.status.in_(["OPEN", "PENDING"]))
        .all()
    )

    # Build blockers list
    blockers: List[str] = []

    if missing_required:
        blockers.append("missing_required_research")

    if property_data.get("ownership_unverified", True):
        blockers.append("ownership_not_verified")

    if record.distress_score < 50:
        blockers.append("distress_score_below_outreach_threshold")

    if record.research_status in ["DO_NOT_CONTACT", "OUTREACH_BLOCKED"]:
        blockers.append("property_status_blocks_outreach")

    if open_tasks:
        blockers.append("research_tasks_still_open")

    # If blockers exist, return NOT_READY
    if blockers:
        return {
            "status": "NOT_READY_FOR_OUTREACH",
            "property_intel_id": property_intel_id,
            "blockers": blockers,
            "missing_required": missing_required,
            "missing_recommended": missing_recommended,
            "open_task_count": len(open_tasks),
            "distress_score": record.distress_score,
            "research_status": record.research_status,
            "next_action": "Complete required research and resolve blockers.",
        }

    # All checks pass: mark property ready and return success
    updated_record = mark_property_ready_for_outreach(db, property_intel_id)

    return {
        "status": "READY_FOR_OUTREACH",
        "property_intel_id": property_intel_id,
        "missing_recommended": missing_recommended,
        "distress_score": updated_record.distress_score if updated_record else record.distress_score,
        "research_status": updated_record.research_status if updated_record else record.research_status,
        "outreach_allowed": updated_record.outreach_allowed if updated_record else record.outreach_allowed,
        "next_action": "Generate owner outreach approval packet.",
    }
