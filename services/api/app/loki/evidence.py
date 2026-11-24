"""Canonical hashing shared by the independent process and API."""
import hashlib
import json

from fastapi import HTTPException


def artifact_digest(artifact_type: str, reference: str | None, content: dict) -> str:
    wrapped = {"artifact_type": artifact_type, "reference": reference, "content": content}
    try:
        canonical = json.dumps(wrapped, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Artifact must be canonical JSON") from None
    return hashlib.sha256(canonical.encode()).hexdigest()




def findings_digest(review_id: str, proposal_sha256: str, reviewer_id: str, analysis_ref: str,
                    summary: str, severity: str, findings: list[dict]) -> str:
    return artifact_digest("loki_result", review_id, {
        "proposal_sha256": proposal_sha256, "reviewer_id": reviewer_id,
        "analysis_ref": analysis_ref, "summary": summary, "severity": severity,
        "findings": sorted(findings, key=lambda item: item["id"]),
    })
