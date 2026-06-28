from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.heimdall.services.property_intel_service import (
    create_property_intel_record,
)
from app.heimdall.services.property_research_task_generator import (
    generate_property_research_tasks,
)


def bulk_create_property_intel_records(
    db: Session,
    records: List[Dict[str, Any]],
    created_by: str = "heimdall",
) -> Dict[str, Any]:
    """
    Bulk create property intel records from driving-for-dollars list.
    
    Steps:
    1. Iterate through each record
    2. Validate required fields (address, city)
    3. Create property intel record
    4. Catch and log any failures
    5. Return summary with created + failed
    
    Input: List of dicts with:
    - address: {address, city, province_or_state, country}
    - property_data: {distress signals, ownership status, etc.}
    
    Output: Created count, failed count, details for each
    """

    created = []
    failed = []

    for item in records:
        address_payload = item.get("address", {})
        property_data = item.get("property_data", {})

        # Validate required fields
        if not address_payload.get("address") or not address_payload.get("city"):
            failed.append(
                {
                    "input": item,
                    "reason": "Missing required address or city.",
                }
            )
            continue

        try:
            # Create property intel record
            record = create_property_intel_record(
                db=db,
                address_payload={
                    **address_payload,
                    "created_by": created_by,
                },
                property_data=property_data,
            )

            # Auto-generate research tasks for this property
            task_result = generate_property_research_tasks(
                db=db,
                property_intel_id=record.id,
                created_by=created_by,
            )

            # Add to success list
            created.append(
                {
                    "id": record.id,
                    "address": record.address,
                    "city": record.city,
                    "research_status": record.research_status,
                    "distress_score": record.distress_score,
                    "lead_lane": record.lead_lane,
                    "outreach_allowed": record.outreach_allowed,
                    "ownership_verified": record.ownership_verified,
                    "research_tasks_created": task_result.get("tasks_created_count", 0),
                }
            )
        except Exception as exc:
            # Add to failure list
            failed.append(
                {
                    "input": item,
                    "reason": str(exc),
                }
            )

    return {
        "status": "BULK_PROPERTY_ENRICHMENT_COMPLETE",
        "created_count": len(created),
        "failed_count": len(failed),
        "created": created,
        "failed": failed,
    }
