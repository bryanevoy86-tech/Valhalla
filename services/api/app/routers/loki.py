"""Loki AI review FastAPI router for artifact analysis and compliance checks."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.loki.review_service import artifact_digest, record_reconsideration, reviewer_identity, verdict
from app.services.prime_business_execution import require_owner_mandate_key
from app.loki.models import LokiReview, LokiReviewStatus
from app.loki.schemas import (
    LokiFindingRead,
    LokiReviewCreate,
    LokiReviewListItem,
    LokiReviewRead,
    LokiVerdict,
    OwnerReconsiderationIn,
)
from app.core.loki_engine import engine as counter_engine
from app.schemas.loki_analysis import (
    LokiAnalysisRequest,
    LokiAnalysisResponse,
)

router = APIRouter(prefix="/loki", tags=["Loki Reviews"], dependencies=[Depends(require_prime_control_key)])


@router.post(
    "/reviews",
    response_model=LokiReviewRead,
    status_code=status.HTTP_201_CREATED,
)
def create_loki_review(
    payload: LokiReviewCreate,
    db: Session = Depends(get_db),
) -> LokiReviewRead:
    """Queue a versioned artifact for the independent worker."""
    reviewer_identity()
    digest = artifact_digest(payload.artifact_type, payload.heimdall_reference_id, payload.raw_input)
    previous = db.query(LokiReview).filter_by(artifact_sha256=digest).one_or_none()
    if previous is not None:
        return previous
    review = LokiReview(
        artifact_type=payload.artifact_type, input_source=payload.input_source,
        risk_profile=payload.risk_profile, raw_input=payload.raw_input,
        heimdall_reference_id=payload.heimdall_reference_id, human_reference_id=payload.human_reference_id,
        status=LokiReviewStatus.QUEUED, artifact_sha256=digest,
    )
    db.add(review)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        previous = db.query(LokiReview).filter_by(artifact_sha256=digest).one_or_none()
        if previous is None:
            raise
        return previous
    return review


@router.post("/reviews/{review_id}/reconsider", dependencies=[Depends(require_owner_mandate_key)])
def reconsider_review(review_id: UUID, payload: OwnerReconsiderationIn, db: Session = Depends(get_db)):
    result = record_reconsideration(db, review_id, payload)
    return {"review_id": result.review_id, "disposition": result.disposition, "artifact_sha256": result.artifact_sha256}


@router.get(
    "/reviews/{review_id}",
    response_model=LokiReviewRead,
)
def get_loki_review(
    review_id: UUID,
    db: Session = Depends(get_db),
) -> LokiReviewRead:
    """Get a specific Loki review by ID."""
    result = db.execute(
        select(LokiReview).where(LokiReview.id == review_id).options()
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Loki review not found")

    return review


@router.get(
    "/reviews",
    response_model=list[LokiReviewListItem],
)
def list_loki_reviews(
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    artifact_type: Optional[str] = None,
    input_source: Optional[str] = None,
    result_severity: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[LokiReviewListItem]:
    """List Loki reviews with optional filters."""
    stmt = select(LokiReview).order_by(LokiReview.created_at.desc())

    if status_filter:
        stmt = stmt.where(LokiReview.status == status_filter)
    if artifact_type:
        stmt = stmt.where(LokiReview.artifact_type == artifact_type)
    if input_source:
        stmt = stmt.where(LokiReview.input_source == input_source)
    if result_severity:
        stmt = stmt.where(LokiReview.result_severity == result_severity)

    stmt = stmt.limit(limit).offset(offset)

    result = db.execute(stmt)
    reviews = result.scalars().all()
    return [
        LokiReviewListItem(
            id=r.id,
            created_at=r.created_at,
            artifact_type=r.artifact_type,
            input_source=r.input_source,
            status=r.status,
            result_severity=r.result_severity,
            summary=r.summary,
        )
        for r in reviews
    ]


@router.get(
    "/reviews/{review_id}/findings",
    response_model=list[LokiFindingRead],
)
def list_loki_findings(
    review_id: UUID,
    db: Session = Depends(get_db),
) -> list[LokiFindingRead]:
    """Return findings only when their complete review receipt verifies."""
    review = db.get(LokiReview, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Loki review not found")
    verdict(db, review)
    return review.findings


@router.get(
    "/reviews/{review_id}/verdict",
    response_model=LokiVerdict,
)
def get_loki_verdict(
    review_id: UUID,
    db: Session = Depends(get_db),
) -> LokiVerdict:
    """Get the final verdict/decision for a Loki review."""
    result = db.execute(
        select(LokiReview).where(LokiReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Loki review not found")

    if review.status != LokiReviewStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="LOKI_AUDIT_NOT_COMPLETE")
    try:
        reviewer_identity()
    except HTTPException:
        raise HTTPException(status_code=503, detail="LOKI_VERIFIED_VERDICT_PROVIDER_NOT_CONNECTED") from None
    return verdict(db, review)


@router.post(
    "/analyze",
    response_model=LokiAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_artifact(
    payload: LokiAnalysisRequest,
    db: Session = Depends(get_db),  # retained for future linkage / logging
) -> LokiAnalysisResponse:
    """Deep counter-analysis of an arbitrary artifact text using LokiCounterEngine.

    This is Pack 81 logic. Currently heuristic and stateless; can be extended to
    persist results or emit events later.
    """
    context = payload.context or {}
    if payload.risk_profile:
        context["risk_profile"] = payload.risk_profile

    result = counter_engine.analyze(
        artifact_text=payload.artifact_text,
        context=context,
    )
    return LokiAnalysisResponse(**result.__dict__)
