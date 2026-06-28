from typing import Any, Dict

from sqlalchemy.orm import Session

from app.heimdall.services.property_intel_service import (
    get_property_intel_record,
    convert_property_to_lead_payload,
    mark_converted_to_lead,
)
from app.heimdall.services.persistence_service import create_deal


def run_property_to_lead_conversion(
    db: Session,
    property_intel_id: str,
    created_by: str = "heimdall",
) -> Dict[str, Any]:
    """
    Convert researched property into real lead and create deal record.
    
    Steps:
    1. Load property intel record
    2. Validate status is READY_FOR_OUTREACH (or similar final states)
    3. Validate outreach_allowed=true
    4. Convert to lead payload
    5. Create deal record with source=property_intel
    6. Mark property as converted_to_lead
    
    Returns deal_id for further underwriting.
    """
    
    # Step 1: Load property record
    record = get_property_intel_record(db, property_intel_id)

    if not record:
        return {
            "status": "ERROR",
            "reason": "Property intel record not found.",
            "property_intel_id": property_intel_id,
        }

    # Step 2: Validate status is ready for conversion
    if record.research_status not in [
        "READY_FOR_OUTREACH",
        "CONVERTED_TO_LEAD",
        "RESEARCH_UPDATED",
    ]:
        return {
            "status": "BLOCKED",
            "reason": "Property is not ready to convert into a lead.",
            "research_status": record.research_status,
            "required_status": "READY_FOR_OUTREACH",
        }

    # Step 3: Validate outreach is allowed
    if not record.outreach_allowed:
        return {
            "status": "BLOCKED",
            "reason": "Outreach is not allowed for this property.",
        }

    # Step 4: Convert to lead payload
    lead_payload = convert_property_to_lead_payload(record)

    # Step 5: Create deal record with source=property_intel
    deal_record = create_deal(
        db,
        {
            "property_address": record.address,
            "state": "NEW_LEAD",
            "source": "property_intel",
            "source_property_intel_id": record.id,
            "created_by": created_by,
            "lead": lead_payload,
            "property_intel": {
                "distress_score": record.distress_score,
                "lead_lane": record.lead_lane,
                "research_status": record.research_status,
                "property_data": record.property_data,
                "distress_analysis": record.distress_analysis,
            },
        },
    )

    # Step 6: Mark property as converted
    mark_converted_to_lead(db, property_intel_id)

    return {
        "status": "PROPERTY_CONVERTED_TO_LEAD",
        "property_intel_id": property_intel_id,
        "deal_id": deal_record.id,
        "lead_payload": lead_payload,
        "next_steps": [
            "Collect seller response details.",
            "Fill underwriting fields.",
            "Run POST /heimdall/intake-db/deal when underwriting and market data are ready.",
        ],
    }
