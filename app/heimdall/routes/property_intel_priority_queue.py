"""
Property Intel Priority Queue Route
Prefix: /heimdall/property-priority
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.property_intel_priority_queue import (
    get_property_priority_queue,
)

router = APIRouter(
    prefix="/heimdall/property-priority",
    tags=["Heimdall Property Priority Queue"],
)


@router.get("/queue")
def property_priority_queue(db: Session = Depends(get_db)):
    """
    Get all properties ranked by research priority.

    **Scoring (0-100):**
    - Distress score: 0-50 points (capped at 50)
    - High priority lane: +20
    - Outreach allowed: +10
    - Ownership verified: +10
    - Vacant/boarded signal: +10
    - Tax arrears signal: +10
    - Absentee owner signal: +5

    **Priority Bands:**
    - URGENT_RESEARCH: Score ≥80
    - HIGH_PRIORITY: Score 60-79
    - MEDIUM_PRIORITY: Score 40-59
    - LOW_PRIORITY: Score 20-39
    - DO_NOT_WORK_NOW: Score <20

    **Blocked Status:**
    - Properties with status in (DO_NOT_CONTACT, OUTREACH_BLOCKED, CONVERTED_TO_LEAD) score to 0

    **Response:**
    ```json
    {
        "count": 42,
        "top_property": {
            "property_intel_id": "propintel_abc123",
            "address": "123 Main St",
            "city": "Toronto",
            "priority_score": 95,
            "priority_band": "URGENT_RESEARCH",
            "distress_score": 85,
            "reasons": ["Distress score: 85", "Tax arrears signal"]
        },
        "priority_queue": [top_property, ...all_properties_ranked]
    }
    ```
    """
    return get_property_priority_queue(db)
