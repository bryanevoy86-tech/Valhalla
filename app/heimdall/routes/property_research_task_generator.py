"""
Property Intel Research Task Generator Route
Prefix: /heimdall/property-research-tasks
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.property_research_task_generator import (
    generate_property_research_tasks,
)

router = APIRouter(
    prefix="/heimdall/property-research-tasks",
    tags=["Heimdall Research Tasks"],
)


@router.post("/generate")
def generate_research_tasks(
    property_intel_id: int,
    created_by: str = "heimdall",
    db: Session = Depends(get_db),
):
    """
    Generate standard research task set for a property.

    Creates 6 standard research tasks:
    1. Verify Property Ownership - Check title records
    2. Check Property Assessment & Tax Records - Look for arrears
    3. Check Recent Sales & Comparables - Estimate ARV
    4. Collect Property Photos - Visual assessment
    5. Verify Outreach Eligibility - Legal/compliance check
    6. Research Property Condition - Assess from records + photos

    **Each task:**
    - Status: OPEN
    - Assigned to VA (VA_DUE_DILIGENCE or VA_SELLER_SUPPORT)
    - Contains property_intel_id + context in data JSON
    - Priority: HIGH or MEDIUM based on task type

    **Response:**
    ```json
    {
        "status": "RESEARCH_TASKS_CREATED",
        "property_intel_id": 42,
        "property_address": "123 Main St Toronto",
        "tasks_created_count": 6,
        "tasks": [
            {
                "id": "uuid-1",
                "title": "Verify Property Ownership",
                "priority": "HIGH",
                "owner_role": "VA_DUE_DILIGENCE",
                "task_type": "verify_ownership",
                "status": "OPEN",
                "data": {...}
            },
            ...
        ]
    }
    ```

    **Query Parameters:**
    - `property_intel_id` (required): Property to generate tasks for
    - `created_by` (optional): Audit trail identifier, default "heimdall"
    """

    result = generate_property_research_tasks(
        db=db,
        property_intel_id=property_intel_id,
        created_by=created_by,
    )

    if result.get("status") == "ERROR":
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "Failed to generate research tasks"),
        )

    return result
