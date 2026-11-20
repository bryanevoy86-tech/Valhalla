"""Independent reviewer receipts and the policy for reconsidering findings."""

import hashlib
import hmac
import json
import os
from uuid import UUID

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.loki.models import (
    LokiFinding,
    LokiIndependentReceipt,
    LokiReconsideration,
    LokiReview,
    LokiReviewStatus,
)
from app.loki.schemas import IndependentReviewIn, LokiVerdict, OwnerReconsiderationIn


def reviewer_identity() -> tuple[str, str]:
    key = os.getenv("VALHALLA_LOKI_REVIEWER_KEY", "")
    name = os.getenv("VALHALLA_LOKI_REVIEWER_ID", "").strip()
    forbidden = {
        os.getenv("VALHALLA_PRIME_CONTROL_KEY"),
        os.getenv("VALHALLA_OWNER_MANDATE_KEY"),
        os.getenv("VALHALLA_FACTORY_KEY"),
        settings.BUILDER_KEY,
        settings.SESSION_TOKEN_DEV,
        settings.jwt_secret,
    }
    if not key or key in forbidden or not 1 <= len(name) <= 100:
        raise HTTPException(status_code=503, detail="LOKI_INDEPENDENT_AUDIT_ENGINE_NOT_CONNECTED")
    return key, name


def require_loki_reviewer(provided: str | None = Header(None, alias="X-Loki-Reviewer-Key")) -> str:
    expected, name = reviewer_identity()
    if not provided or not hmac.compare_digest(expected.encode(), provided.encode()):
        raise HTTPException(status_code=401, detail="Loki reviewer authentication required")
    return name


def artifact_digest(artifact_type: str, reference: str | None, content: dict) -> str:
    wrapped = {"artifact_type": artifact_type, "reference": reference, "content": content}
    try:
        canonical = json.dumps(wrapped, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Artifact must be canonical JSON") from None
    return hashlib.sha256(canonical.encode()).hexdigest()


def review_digest(review: LokiReview) -> str:
    return artifact_digest(review.artifact_type, review.heimdall_reference_id, review.raw_input)


def publish_receipt(db: Session, review_id: UUID, reviewer: str, payload: IndependentReviewIn) -> LokiIndependentReceipt:
    review = db.get(LokiReview, review_id, with_for_update=True)
    if review is None:
        raise HTTPException(status_code=404, detail="Loki review not found")
    if review.status != LokiReviewStatus.QUEUED:
        raise HTTPException(status_code=409, detail="Review is no longer queued")
    if review.artifact_sha256 != payload.artifact_sha256 or not hmac.compare_digest(review_digest(review), payload.artifact_sha256):
        raise HTTPException(status_code=409, detail="Review artifact changed")
    for finding in payload.findings:
        db.add(LokiFinding(
            review_id=review.id, category=finding.category, severity=finding.severity,
            message=finding.message, suggested_fix=finding.suggested_fix,
            tags={"material": finding.material or finding.severity == "critical", "evidence_ref": finding.evidence_ref},
        ))
    receipt = LokiIndependentReceipt(
        review_id=review.id, artifact_sha256=payload.artifact_sha256,
        reviewer_id=reviewer, analysis_ref=payload.analysis_ref,
    )
    db.add(receipt)
    review.summary = payload.summary
    review.result_severity = "critical" if any(item.severity == "critical" for item in payload.findings) else (
        "warn" if payload.findings else "ok"
    )
    review.status = LokiReviewStatus.COMPLETED
    db.commit()
    return receipt


def _material(review: LokiReview) -> set[UUID]:
    return {finding.id for finding in review.findings if (finding.tags or {}).get("material") is True}


def record_reconsideration(db: Session, review_id: UUID, payload: OwnerReconsiderationIn) -> LokiReconsideration:
    receipt = db.get(LokiIndependentReceipt, review_id, with_for_update=True)
    if receipt is None:
        raise HTTPException(status_code=409, detail="Independent review receipt required")
    review = db.get(LokiReview, review_id)
    if receipt.artifact_sha256 != review_digest(review) or receipt.artifact_sha256 != payload.artifact_sha256:
        raise HTTPException(status_code=409, detail="Reconsideration must match the reviewed artifact")
    if payload.material_finding_ids != _material(review) or not payload.reason.strip():
        raise HTTPException(status_code=422, detail="Address every material finding and record a reason")
    if payload.disposition == "accept_risk" and review.result_severity == "critical":
        raise HTTPException(status_code=409, detail="Critical findings require revision or rejection")
    if db.get(LokiReconsideration, review_id):
        raise HTTPException(status_code=409, detail="Reconsideration already recorded")
    decision = LokiReconsideration(
        review_id=review_id, artifact_sha256=payload.artifact_sha256, disposition=payload.disposition,
        material_finding_ids=sorted(str(value) for value in payload.material_finding_ids),
        reason=payload.reason.strip(),
    )
    db.add(decision)
    db.commit()
    return decision


def verdict(db: Session, review: LokiReview) -> LokiVerdict:
    if review.status != LokiReviewStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="LOKI_AUDIT_NOT_COMPLETE")
    receipt = db.get(LokiIndependentReceipt, review.id)
    if receipt is None or receipt.artifact_sha256 != review.artifact_sha256 or receipt.artifact_sha256 != review_digest(review):
        raise HTTPException(status_code=503, detail="LOKI_VERIFIED_VERDICT_PROVIDER_NOT_CONNECTED")
    decision = db.get(LokiReconsideration, review.id)
    material = _material(review)
    accepted = bool(
        decision and decision.disposition == "accept_risk" and decision.artifact_sha256 == receipt.artifact_sha256
        and set(decision.material_finding_ids) == {str(value) for value in material}
    )
    ok = review.result_severity != "critical" and (not material or accepted) and (
        decision is None or decision.disposition == "accept_risk"
    )
    return LokiVerdict(
        result_severity=review.result_severity, headline=review.summary or "",
        artifact_sha256=receipt.artifact_sha256, ok_to_proceed=ok,
        reconsideration_status=decision.disposition if decision else ("required" if material else "not_required"),
        requires_human_review=not ok, key_risks=[finding.message for finding in review.findings],
    )
