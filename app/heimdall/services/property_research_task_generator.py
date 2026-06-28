"""
Property Intel Research Task Generator Service

Automatically generate standard research task set for newly discovered properties.
Creates VA tasks like: check assessment, verify ownership, check tax arrears, etc.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.heimdall.models.persistence import HeimdallTask
from app.heimdall.services.property_intel_service import get_property_intel_record


# Standard research task templates
RESEARCH_TASK_TEMPLATES = [
    {
        "title": "Verify Property Ownership",
        "description": "Check title records, verify owner name and contact info accuracy",
        "priority": "HIGH",
        "owner_role": "VA_DUE_DILIGENCE",
        "task_type": "verify_ownership",
    },
    {
        "title": "Check Property Assessment & Tax Records",
        "description": "Retrieve current assessment value and check for tax arrears",
        "priority": "HIGH",
        "owner_role": "VA_DUE_DILIGENCE",
        "task_type": "check_assessment",
    },
    {
        "title": "Check Recent Sales & Comparables",
        "description": "Research recent sales in area, find comparable properties for ARV estimate",
        "priority": "MEDIUM",
        "owner_role": "VA_DUE_DILIGENCE",
        "task_type": "check_recent_sales",
    },
    {
        "title": "Collect Property Photos",
        "description": "Add/update property photos in system for visual assessment",
        "priority": "MEDIUM",
        "owner_role": "VA_DUE_DILIGENCE",
        "task_type": "add_photos",
    },
    {
        "title": "Verify Outreach Eligibility",
        "description": "Confirm legal/compliance requirements met for owner outreach",
        "priority": "HIGH",
        "owner_role": "VA_SELLER_SUPPORT",
        "task_type": "verify_outreach_eligibility",
    },
    {
        "title": "Research Property Condition",
        "description": "Assess property condition from public records and photos",
        "priority": "MEDIUM",
        "owner_role": "VA_DUE_DILIGENCE",
        "task_type": "assess_condition",
    },
]


def generate_property_research_tasks(
    db: Session,
    property_intel_id: int,
    created_by: str = "heimdall",
) -> Dict[str, Any]:
    """
    Generate standard research task set for newly discovered property.

    Creates 6 standard tasks:
    1. Verify ownership
    2. Check assessment & taxes
    3. Check recent sales
    4. Collect photos
    5. Verify outreach eligibility
    6. Research condition

    Each task is OPEN, assigned to appropriate VA role, with property_intel_id stored in data JSON.

    Args:
        db: SQLAlchemy session
        property_intel_id: ID of property_intel record
        created_by: Audit trail user identifier

    Returns:
        {
            "status": "RESEARCH_TASKS_CREATED",
            "property_intel_id": int,
            "property_address": str,
            "tasks_created_count": int,
            "tasks": [
                {
                    "id": int,
                    "title": str,
                    "priority": str,
                    "owner_role": str,
                    "task_type": str,
                    "status": "OPEN",
                    "data": {...}
                }
            ]
        }
    """

    # Fetch property intel record
    property_record = get_property_intel_record(db, property_intel_id)
    if not property_record:
        return {
            "status": "ERROR",
            "error": f"Property intel record {property_intel_id} not found",
            "property_intel_id": property_intel_id,
        }

    property_address = f"{property_record.address} {property_record.city}"

    created_tasks = []

    for template in RESEARCH_TASK_TEMPLATES:
        task_id = str(uuid.uuid4())
        task = HeimdallTask(
            id=task_id,
            deal_id=None,  # Research-phase tasks not yet linked to deal
            title=template["title"],
            status="OPEN",
            priority=template["priority"],
            owner_role=template["owner_role"],
            data={
                "property_intel_id": property_intel_id,
                "task_type": template["task_type"],
                "description": template.get("description"),
                "property_address": property_address,
                "distress_score": property_record.distress_score,
                "lead_lane": property_record.lead_lane,
                "created_by": created_by,
                "created_at_property": property_record.created_at.isoformat() if property_record.created_at else None,
            },
        )
        db.add(task)
        db.flush()  # Flush to get task.id

        created_tasks.append({
            "id": task.id,
            "title": task.title,
            "priority": task.priority,
            "owner_role": task.owner_role,
            "task_type": template["task_type"],
            "status": task.status,
            "data": task.data,
        })

    db.commit()

    return {
        "status": "RESEARCH_TASKS_CREATED",
        "property_intel_id": property_intel_id,
        "property_address": property_address,
        "tasks_created_count": len(created_tasks),
        "tasks": created_tasks,
    }
