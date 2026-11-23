"""Independent reviewer receipts and the policy for reconsidering findings."""

import hmac
import os
from uuid import UUID

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.loki.evidence import artifact_digest
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
        os.getenv("VALHALLA_LOKI_GROQ_KEY"),
        os.getenv("VALHALLA_SPECIALIST_GROQ_KEY"),
        os.getenv("VALHALLA_OWNER_CHAT_GROQ_KEY"),
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


def review_digest(review: LokiReview) -> str:
    return artifact_digest(review.artifact_type, review.heimdall_reference_id, review.raw_input)


def result_digest(review: LokiReview, receipt: LokiIndependentReceipt, findings: list[LokiFinding]) -> str:
    records = [
        {"id": str(item.id), "category": item.category, "severity": item.severity,
         "message": item.message, "suggested_fix": item.suggested_fix, "tags": item.tags}
        for item in sorted(findings, key=lambda item: str(item.id))
    ]
    return artifact_digest("loki_result", str(review.id), {
        "proposal_sha256": receipt.artifact_sha256, "reviewer_id": receipt.reviewer_id,
        "analysis_ref": receipt.analysis_ref, "summary": review.summary, "severity": review.result_severity,
        "findings": records,
    })


def require_result_integrity(review: LokiReview, receipt: LokiIndependentReceipt) -> None:
    if receipt.result_sha256 is None:
        raise HTTPException(409, "Historical Loki review has no authenticated findings digest")
    if not hmac.compare_digest(
        receipt.result_sha256, result_digest(review, receipt, review.findings),
    ):
        raise HTTPException(409, "Loki findings no longer match the published receipt")


def publish_receipt(db: Session, review_id: UUID, reviewer: str, payload: IndependentReviewIn) -> LokiIndependentReceipt:
    review = db.get(LokiReview, review_id, with_for_update=True)
    if review is None:
        raise HTTPException(status_code=404, detail="Loki review not found")
    if review.status != LokiReviewStatus.QUEUED:
        raise HTTPException(status_code=409, detail="Review is no longer queued")
    if review.artifact_sha256 != payload.artifact_sha256 or not hmac.compare_digest(review_digest(review), payload.artifact_sha256):
        raise HTTPException(status_code=409, detail="Review artifact changed")
    findings = [
        LokiFinding(
            review_id=review.id, category=finding.category, severity=finding.severity,
            message=finding.message, suggested_fix=finding.suggested_fix,
            tags={"material": finding.material or finding.severity == "critical", "evidence_ref": finding.evidence_ref},
        )
        for finding in payload.findings
    ]
    db.add_all(findings)
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
    db.flush()
    receipt.result_sha256 = result_digest(review, receipt, findings)
    db.commit()
    return receipt


def _material(review: LokiReview) -> set[UUID]:
    return {finding.id for finding in review.findings if (finding.tags or {}).get("material") is True}


def _decision_digest(decision: LokiReconsideration, receipt: LokiIndependentReceipt) -> str:
    return artifact_digest("loki_owner_disposition", str(decision.review_id), {
        "proposal_sha256": decision.artifact_sha256,
        "result_sha256": receipt.result_sha256,
        "disposition": decision.disposition,
        "material_finding_ids": decision.material_finding_ids,
        "reason": decision.reason,
    })


def record_reconsideration(db: Session, review_id: UUID, payload: OwnerReconsiderationIn) -> LokiReconsideration:
    receipt = db.get(LokiIndependentReceipt, review_id, with_for_update=True)
    if receipt is None:
        raise HTTPException(status_code=409, detail="Independent review receipt required")
    review = db.get(LokiReview, review_id)
    if (review is None or review.status != LokiReviewStatus.COMPLETED
            or receipt.artifact_sha256 != review.artifact_sha256
            or receipt.artifact_sha256 != review_digest(review) or receipt.artifact_sha256 != payload.artifact_sha256):
        raise HTTPException(status_code=409, detail="Reconsideration must match the reviewed artifact")
    require_result_integrity(review, receipt)
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
    decision.decision_sha256 = _decision_digest(decision, receipt)
    db.add(decision)
    db.commit()
    return decision


def verdict(db: Session, review: LokiReview) -> LokiVerdict:
    if review.status != LokiReviewStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="LOKI_AUDIT_NOT_COMPLETE")
    receipt = db.get(LokiIndependentReceipt, review.id)
    if receipt is None or receipt.artifact_sha256 != review.artifact_sha256 or receipt.artifact_sha256 != review_digest(review):
        raise HTTPException(status_code=503, detail="LOKI_VERIFIED_VERDICT_PROVIDER_NOT_CONNECTED")
    require_result_integrity(review, receipt)
    decision = db.get(LokiReconsideration, review.id)
    material = _material(review)
    if decision and (
        not decision.decision_sha256
        or decision.artifact_sha256 != receipt.artifact_sha256
        or decision.material_finding_ids != sorted(str(value) for value in material)
        or not hmac.compare_digest(decision.decision_sha256, _decision_digest(decision, receipt))
    ):
        raise HTTPException(409, "Owner disposition does not bind the current Loki findings")
    ok = review.result_severity != "critical" and (
        decision.disposition == "accept_risk" if decision else not material
    )
    return LokiVerdict(
        result_severity=review.result_severity, headline=review.summary or "",
        artifact_sha256=receipt.artifact_sha256, result_sha256=receipt.result_sha256,
        reconsideration_sha256=decision.decision_sha256 if decision else None, ok_to_proceed=ok,
        reconsideration_status=decision.disposition if decision else ("required" if material else "not_required"),
        requires_human_review=not ok, key_risks=[finding.message for finding in review.findings],
    )
