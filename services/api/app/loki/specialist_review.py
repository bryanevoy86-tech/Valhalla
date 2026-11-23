"""Bind material specialist evidence to separately reviewed versions."""
import re
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.loki.models import LokiReview, LokiReviewStatus
from app.loki.review_service import verdict
from app.models.specialist_assignment import SpecialistAssignment
from app.pantheon.monitor import report_matches_assignment, utc_now, verified_report


def enqueue_report(db: Session, event_id: str) -> LokiReview:
    report = verified_report(db, event_id)
    digest = report.pop("report_sha256")
    prior = db.scalar(select(LokiReview).filter_by(artifact_sha256=digest))
    if prior is not None:
        return prior
    review = LokiReview(
        input_source="pantheon-assignment", artifact_type="pantheon_report", heimdall_reference_id=event_id,
        artifact_sha256=digest, raw_input=report, status=LokiReviewStatus.QUEUED,
    )
    db.add(review)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        prior = db.scalar(select(LokiReview).filter_by(artifact_sha256=digest))
        if prior is None:
            raise
        return prior
    return review


def require_reviewed_reports(db: Session, ids, scope: dict) -> list[dict]:
    if not isinstance(ids, list) or len(ids) > 10 or any(
        not isinstance(value, str) or not re.fullmatch(r"GOD-[a-f0-9]{64}", value) for value in ids
    ) or len(set(ids)) != len(ids):
        raise HTTPException(422, "Supply distinct specialist report IDs")
    verified = []
    for event_id in sorted(ids):
        report = verified_report(db, event_id)
        try:
            assignment_id = UUID(report["assignment_id"])
            observed = datetime.fromisoformat(report["observed_at"])
            if observed.utcoffset() is None:
                raise ValueError
            observed = observed.astimezone(timezone.utc).replace(tzinfo=None)
        except (ValueError, TypeError, KeyError, AttributeError):
            raise HTTPException(409, "Specialist report has invalid assignment or time evidence") from None
        assignment = db.get(SpecialistAssignment, assignment_id, with_for_update=True)
        now = utc_now()
        if (not report_matches_assignment(assignment, report) or report["scope"] != scope
                or report.get("status") != "observed" or assignment.state != "active" or assignment.expires_at <= now
                or not 0 <= (now - observed).total_seconds() <= 2 * assignment.cadence_seconds):
            raise HTTPException(409, "Specialist report is stale, revoked or outside decision scope")
        review = db.scalar(select(LokiReview).filter_by(
            artifact_type="pantheon_report", artifact_sha256=report["report_sha256"], heimdall_reference_id=event_id,
        ))
        decision = verdict(db, review) if review is not None else None
        if decision is None or not decision.ok_to_proceed:
            raise HTTPException(409, "Specialist report requires independent Loki reconsideration")
        verified.append({
            "report_event_id": event_id, "review_id": str(review.id), "sha256": report["report_sha256"],
            "result_sha256": decision.result_sha256, "reconsideration_sha256": decision.reconsideration_sha256,
        })
    return verified
