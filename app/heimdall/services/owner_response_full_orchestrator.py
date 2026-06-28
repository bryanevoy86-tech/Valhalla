from typing import Any, Dict

from sqlalchemy.orm import Session

from app.heimdall.services.owner_response_service import intake_owner_response
from app.heimdall.services.owner_response_lead_trigger import (
    trigger_lead_conversion_from_owner_response,
)


def run_owner_response_full_orchestrator(
    db: Session,
    property_intel_id: str,
    response_text: str,
    response_channel: str = "unknown",
    received_by: str = "heimdall",
    auto_trigger_lead_conversion: bool = True,
) -> Dict[str, Any]:
    """
    Full orchestration: Owner response → Classification → Task Creation → Lead Conversion.
    
    Steps:
    1. Intake owner response (classify + update property status + create tasks)
    2. If auto_trigger_lead_conversion=true and status allows:
       → Trigger lead conversion
       → Create deal record
    3. Return combined results with next actions
    
    One call handles:
    - Response classification (yes, maybe, no, stop, wrong contact, unclear)
    - Property status update
    - Task creation (call, follow-up, verify, review)
    - Automatic lead conversion if safe
    """

    # Step 1: Process owner response
    response_result = intake_owner_response(
        db=db,
        property_intel_id=property_intel_id,
        response_text=response_text,
        response_channel=response_channel,
        received_by=received_by,
    )

    # Step 2: If error, return early
    if response_result.get("status") == "ERROR":
        return {
            "status": "ERROR",
            "response_result": response_result,
        }

    # Step 3: Optionally trigger lead conversion
    conversion_result = None
    if auto_trigger_lead_conversion:
        conversion_result = trigger_lead_conversion_from_owner_response(
            db=db,
            property_intel_id=property_intel_id,
            triggered_by=received_by,
        )

    # Step 4: Return combined orchestration result
    return {
        "status": "OWNER_RESPONSE_ORCHESTRATED",
        "property_intel_id": property_intel_id,
        "response_result": response_result,
        "conversion_result": conversion_result,
        "human_review_required": response_result.get("human_review_required", True),
        "next_action": response_result.get("next_action"),
    }
