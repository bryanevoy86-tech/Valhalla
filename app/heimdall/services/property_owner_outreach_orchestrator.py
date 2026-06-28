from typing import Any, Dict

from sqlalchemy.orm import Session

from app.heimdall.services.property_intel_service import (
    get_property_intel_record,
    mark_property_ready_for_outreach,
)
from app.heimdall.services.owner_outreach_approval_service import (
    create_owner_outreach_approval,
)


def serialize_property_record(record) -> Dict[str, Any]:
    """Convert SQLAlchemy property intel record to dict."""
    return {
        "id": record.id,
        "address": record.address,
        "city": record.city,
        "province_or_state": record.province_or_state,
        "country": record.country,
        "research_status": record.research_status,
        "distress_score": record.distress_score,
        "lead_lane": record.lead_lane,
        "ownership_verified": record.ownership_verified,
        "outreach_allowed": record.outreach_allowed,
        "converted_to_lead": record.converted_to_lead,
        "raw_address_payload": record.raw_address_payload,
        "property_data": record.property_data,
        "research_plan": record.research_plan,
        "distress_analysis": record.distress_analysis,
        "notes": record.notes,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


def run_property_owner_outreach_orchestrator(
    db: Session,
    property_intel_id: str,
    created_by: str = "heimdall",
) -> Dict[str, Any]:
    """
    Full orchestration: Property Intel → Readiness Check → Owner Outreach.
    
    Steps:
    1. Load property intel record from database
    2. Check outreach readiness (ownership verified, distress ≥50, etc.)
    3. If blocked: return OUTREACH_BLOCKED with reasons
    4. If approved: generate owner letter + create approval + create message draft
    5. Block sending until approval is granted
    
    Returns complete result with approval_id, message_id, and draft letter.
    """
    
    # Step 1: Load property record
    record = get_property_intel_record(db, property_intel_id)

    if not record:
        return {
            "status": "ERROR",
            "reason": "Property intel record not found.",
            "property_intel_id": property_intel_id,
        }

    # Step 2: Check readiness (validates gates + updates status)
    readiness_record = mark_property_ready_for_outreach(db, property_intel_id)

    if not readiness_record:
        return {
            "status": "ERROR",
            "reason": "Could not update outreach readiness.",
            "property_intel_id": property_intel_id,
        }

    property_record = serialize_property_record(readiness_record)

    # Step 3: If blocked, return with blockers
    if readiness_record.research_status != "READY_FOR_OUTREACH":
        return {
            "status": "OUTREACH_BLOCKED",
            "reason": "Property did not pass outreach readiness gates.",
            "property": property_record,
            "blocked_actions": [
                "Do not send letter.",
                "Do not email owner.",
                "Do not convert to active lead yet.",
            ],
        }

    # Step 4: Generate letter + create approval + create message
    approval_result = create_owner_outreach_approval(
        db=db,
        property_record=property_record,
        created_by=created_by,
    )

    if approval_result.get("status") == "BLOCKED":
        return {
            "status": "OUTREACH_BLOCKED",
            "reason": approval_result.get("reason"),
            "property": property_record,
            "approval_result": approval_result,
        }

    # Step 5: Return complete orchestration result
    return {
        "status": "OWNER_OUTREACH_READY_FOR_APPROVAL",
        "property": property_record,
        "approval_result": approval_result,
        "next_steps": [
            "Review owner outreach letter.",
            "Approve or reject the outreach approval.",
            "If approved, run message send gate.",
            "Only send after message status becomes READY_TO_SEND.",
        ],
        "send_blocked_until_approved": True,
    }
