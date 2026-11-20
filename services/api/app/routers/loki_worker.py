"""Restricted interface for the independently deployed Loki reviewer."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.loki.models import LokiReview, LokiReviewStatus
from app.loki.review_service import publish_receipt, require_loki_reviewer, review_digest
from app.loki.schemas import IndependentReviewIn

router = APIRouter(prefix="/loki/worker", tags=["Loki Worker"])


@router.get("/reviews", dependencies=[Depends(require_loki_reviewer)])
def queued_reviews(limit: int = Query(25, ge=1, le=100), db: Session = Depends(get_db)):
    queue = (
        db.query(LokiReview).filter(LokiReview.status == LokiReviewStatus.QUEUED, LokiReview.artifact_sha256.is_not(None))
        .order_by(LokiReview.created_at, LokiReview.id).limit(limit).all()
    )
    return [
        {
            "review_id": review.id, "artifact_type": review.artifact_type,
            "reference": review.heimdall_reference_id, "raw_input": review.raw_input,
            "artifact_sha256": review_digest(review),
        }
        for review in queue
    ]


@router.post("/reviews/{review_id}/result", status_code=201)
def complete_review(
    review_id: UUID, payload: IndependentReviewIn, reviewer: str = Depends(require_loki_reviewer),
    db: Session = Depends(get_db),
):
    receipt = publish_receipt(db, review_id, reviewer, payload)
    return {"review_id": receipt.review_id, "artifact_sha256": receipt.artifact_sha256, "analysis_ref": receipt.analysis_ref}
