from typing import Any, Dict

from sqlalchemy.orm import Session

from app.heimdall.services.property_intel_service import get_property_intel_record
from app.heimdall.services.property_to_lead_orchestrator import (
    run_property_to_lead_conversion,
)


CONVERTIBLE_STATUSES = [
    "OWNER_INTERESTED",
    "OWNER_MAYBE",
]


BLOCKED_STATUSES = [
    "DO_NOT_CONTACT",
    "VERIFY_OWNER_DATA",
    "OWNER_RESPONSE_MANUAL_REVIEW",
]


def trigger_lead_conversion_from_owner_response(
    db: Session,
    property_intel_id: str,
    triggered_by: str = "heimdall",
) -> Dict[str, Any]:
    """
    Trigger lead conversion after positive owner response.
    
    Steps:
    1. Load property intel record
    2. Check status is OWNER_INTERESTED or OWNER_MAYBE
    3. Reject if status in BLOCKED_STATUSES (DO_NOT_CONTACT, etc.)
    4. Validate outreach_allowed=true
    5. Call property-to-lead conversion
    6. Return deal_id if conversion succeeded
    
    Allowed transitions:
    - OWNER_INTERESTED → Convert to lead + deal intake
    - OWNER_MAYBE → Convert to lead + deal intake
    
    Blocked transitions:
    - DO_NOT_CONTACT → Never convert (hard stop)
    - VERIFY_OWNER_DATA → Manual review required first
    - OWNER_RESPONSE_MANUAL_REVIEW → Manual review required first
    """

    # Step 1: Load property record
    record = get_property_intel_record(db, property_intel_id)

    if not record:
        return {
            "status": "ERROR",
            "reason": "Property intel record not found.",
            "property_intel_id": property_intel_id,
        }

    # Step 2: Check if status blocks conversion
    if record.research_status in BLOCKED_STATUSES:
        return {
            "status": "BLOCKED",
            "reason": "Property response status blocks lead conversion.",
            "research_status": record.research_status,
            "property_intel_id": property_intel_id,
        }

    # Step 3: Check if status allows conversion
    if record.research_status not in CONVERTIBLE_STATUSES:
        return {
            "status": "NOT_READY",
            "reason": "Owner has not shown enough interest to convert.",
            "research_status": record.research_status,
            "property_intel_id": property_intel_id,
        }

    # Step 4: Validate outreach_allowed flag
    if not record.outreach_allowed:
        return {
            "status": "BLOCKED",
            "reason": "Outreach is not allowed. Lead conversion blocked.",
            "research_status": record.research_status,
            "property_intel_id": property_intel_id,
        }

    # Step 5: Convert to lead
    result = run_property_to_lead_conversion(
        db=db,
        property_intel_id=property_intel_id,
        created_by=triggered_by,
    )

    return {
        "status": "LEAD_CONVERSION_TRIGGERED",
        "property_intel_id": property_intel_id,
        "conversion_result": result,
    }
