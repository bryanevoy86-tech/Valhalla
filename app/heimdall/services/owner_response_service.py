from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.heimdall.education.owner_response_engine import build_owner_response_result
from app.heimdall.services.property_intel_service import get_property_intel_record
from app.heimdall.services.persistence_service import create_task


def intake_owner_response(
    db: Session,
    property_intel_id: str,
    response_text: str,
    response_channel: str = "unknown",
    received_by: str = "heimdall",
) -> Dict[str, Any]:
    """
    Intake owner response and update property/lead status.
    
    Steps:
    1. Load property intel record
    2. Classify response (yes, maybe, no, stop, wrong contact, unclear)
    3. Update property status based on classification
    4. Create tasks for follow-up actions
    5. Log response in notes (audit trail)
    6. Set human_review_required flag if needed
    
    Response types and actions:
    - DO_NOT_CONTACT: Set outreach_allowed=false, status=DO_NOT_CONTACT
    - INTERESTED: status=OWNER_INTERESTED, create CRITICAL call task
    - MAYBE: status=OWNER_MAYBE, create HIGH follow-up task
    - NOT_INTERESTED: status=NURTURE_OR_CLOSE
    - WRONG_CONTACT: status=VERIFY_OWNER_DATA, create HIGH verification task
    - UNCLEAR: status=OWNER_RESPONSE_MANUAL_REVIEW, create MEDIUM review task
    """

    # Step 1: Load property record
    record = get_property_intel_record(db, property_intel_id)
    if not record:
        return {
            "status": "ERROR",
            "reason": "Property intel record not found.",
        }

    # Step 2: Classify response
    result = build_owner_response_result(
        property_intel_id=property_intel_id,
        response_text=response_text,
        response_channel=response_channel,
    )

    classification = result["classification"]
    response_type = classification["response_type"]

    # Step 3: Log response in audit trail
    note = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "owner_response",
        "response_text": response_text,
        "response_channel": response_channel,
        "classification": classification,
        "received_by": received_by,
    }
    record.notes = (record.notes or []) + [note]

    # Step 4: Update property status and create tasks based on classification
    if response_type == "DO_NOT_CONTACT":
        # Hard stop: block all future outreach
        record.outreach_allowed = False
        record.research_status = "DO_NOT_CONTACT"

    elif response_type == "INTERESTED":
        # Hot lead: create critical call task
        record.research_status = "OWNER_INTERESTED"
        create_task(
            db,
            {
                "deal_id": record.id,
                "title": "Call interested property owner",
                "status": "OPEN",
                "priority": "critical",
                "owner_role": "BRYAN_OR_ACQUISITIONS",
                "property_address": record.address,
                "notes": "Owner showed interest. Call quickly and qualify.",
            },
        )

    elif response_type == "MAYBE":
        # Warm lead: create follow-up task
        record.research_status = "OWNER_MAYBE"
        create_task(
            db,
            {
                "deal_id": record.id,
                "title": "Follow up with maybe-interested owner",
                "status": "OPEN",
                "priority": "high",
                "owner_role": "VA_SELLER_SUPPORT",
                "property_address": record.address,
                "notes": "Owner may be interested. Ask timeline, price, condition, authority.",
            },
        )

    elif response_type == "NOT_INTERESTED":
        # Cold lead: nurture or archive
        record.research_status = "NURTURE_OR_CLOSE"

    elif response_type == "WRONG_CONTACT":
        # Data issue: verify owner info
        record.research_status = "VERIFY_OWNER_DATA"
        create_task(
            db,
            {
                "deal_id": record.id,
                "title": "Verify owner/contact data",
                "status": "OPEN",
                "priority": "high",
                "owner_role": "VA_DUE_DILIGENCE",
                "property_address": record.address,
                "notes": "Owner response indicates wrong person/contact.",
            },
        )

    else:  # UNCLEAR
        # Unknown: manual review
        record.research_status = "OWNER_RESPONSE_MANUAL_REVIEW"
        create_task(
            db,
            {
                "deal_id": record.id,
                "title": "Manual review owner response",
                "status": "OPEN",
                "priority": "medium",
                "owner_role": "BRYAN_OR_ACQUISITIONS",
                "property_address": record.address,
                "notes": response_text,
            },
        )

    # Step 5: Commit all changes
    record.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(record)

    return {
        "status": "OWNER_RESPONSE_PROCESSED",
        "property_intel_id": property_intel_id,
        "property_status": record.research_status,
        "classification": classification,
        "human_review_required": result["human_review_required"],
        "next_action": classification["next_action"],
    }
