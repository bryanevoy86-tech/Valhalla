from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.outcome_feedback_service import (
    record_deal_outcome,
)

router = APIRouter(
    prefix="/heimdall/outcomes",
    tags=["Heimdall Outcomes"],
)


class OutcomeFeedbackRequest(BaseModel):
    outcome_payload: Dict[str, Any]


@router.post("/{deal_id}")
def outcome_feedback(
    deal_id: str,
    payload: OutcomeFeedbackRequest,
    db: Session = Depends(get_db),
):
    return record_deal_outcome(
        db=db,
        deal_id=deal_id,
        outcome_payload=payload.outcome_payload,
    )
