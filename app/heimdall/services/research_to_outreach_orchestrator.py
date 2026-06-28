from typing import Any, Dict

from sqlalchemy.orm import Session

from app.heimdall.services.research_readiness_service import (
    evaluate_research_readiness,
)
from app.heimdall.services.owner_outreach_approval_service import (
    create_owner_outreach_approval,
)
from app.heimdall.services.property_intel_service import (
    get_property_intel_record,
)


def serialize_property_record(record) -> Dict[str, Any]:
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


def run_research_to_outreach(
    db: Session,
    property_intel_id: str,
    created_by: str = "heimdall",
) -> Dict[str, Any]:
    readiness = evaluate_research_readiness(
        db=db,
        property_intel_id=property_intel_id,
    )

    if readiness.get("status") != "READY_FOR_OUTREACH":
        return {
            "status": "OUTREACH_NOT_READY",
            "property_intel_id": property_intel_id,
            "readiness": readiness,
            "next_action": "Complete research blockers before drafting outreach.",
        }

    record = get_property_intel_record(db, property_intel_id)
    if not record:
        return {
            "status": "ERROR",
            "reason": "Property intel record not found after readiness check.",
        }

    property_record = serialize_property_record(record)

    approval_result = create_owner_outreach_approval(
        db=db,
        property_record=property_record,
        created_by=created_by,
    )

    return {
        "status": "OUTREACH_APPROVAL_CREATED",
        "property_intel_id": property_intel_id,
        "readiness": readiness,
        "approval_result": approval_result,
        "send_blocked_until_approved": True,
        "next_steps": [
            "Review owner outreach approval.",
            "Approve or reject letter.",
            "Run message send gate after approval.",
        ],
    }
