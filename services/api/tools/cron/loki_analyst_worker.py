#!/usr/bin/env python3
"""Run the independent local Loki analyst against the restricted queue."""
import argparse
from datetime import datetime, timezone
import json
import os
import signal
import threading
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import httpx

from business_factory_worker import poll
from app.loki.analyst import challenge
from app.loki.evidence import findings_digest


def matches_findings(receipt: dict, review_id: UUID, reviewer_id: str, result) -> bool:
    ids = receipt.get("finding_ids")
    if not isinstance(ids, list) or len(ids) != len(result.findings):
        return False
    try:
        if any(not isinstance(value, str) or str(UUID(value)) != value for value in ids):
            return False
    except ValueError:
        return False
    if len(ids) != len(set(ids)):
        return False
    findings = [
        {"id": finding_id, "category": finding.category, "severity": finding.severity,
         "message": finding.message, "suggested_fix": finding.suggested_fix,
         "tags": {"material": finding.material or finding.severity == "critical", "evidence_ref": finding.evidence_ref}}
        for finding_id, finding in zip(ids, result.findings, strict=True)
    ]
    severity = "critical" if any(finding.severity == "critical" for finding in result.findings) else (
        "warn" if result.findings else "ok"
    )
    return receipt.get("result_sha256") == findings_digest(
        str(review_id), result.artifact_sha256, reviewer_id, result.analysis_ref, result.summary, severity, findings,
    )


def tick(client: httpx.Client, kind: str, reviewer_id: str) -> dict:
    response = client.get("/loki/worker/reviews", params={"limit": 1, "artifact_type": kind})
    response.raise_for_status()
    pending = response.json()
    if not pending:
        return {"status": "idle"}
    item = pending[0]
    if item.get("artifact_type") != kind:
        raise RuntimeError("Loki queue returned a different artifact type")
    review_id = UUID(item["review_id"])
    result = challenge(item)
    published = client.post(f"/loki/worker/reviews/{review_id}/result", json=result.model_dump(mode="json"))
    if published.status_code == 409:
        return {"status": "blocked", "verified": False}
    published.raise_for_status()
    receipt = published.json()
    if (not isinstance(receipt, dict) or published.status_code != 201 or receipt.get("review_id") != str(review_id)
            or receipt.get("artifact_sha256") != result.artifact_sha256
            or receipt.get("analysis_ref") != result.analysis_ref or receipt.get("reviewer_id") != reviewer_id
            or not matches_findings(receipt, review_id, reviewer_id, result)):
        raise RuntimeError("Loki publication receipt does not match the submitted review")
    return {"status": "reviewed", "verified": True, "review_id": str(review_id),
            "artifact_sha256": result.artifact_sha256, "result_sha256": receipt["result_sha256"],
            "reviewer_id": reviewer_id, "findings": len(result.findings)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-type", default="universal_opportunity",
                        choices=("universal_opportunity", "pantheon_report", "economic_advice", "personal_allocation",
                                 "acquisition_comparison"))
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=15, choices=range(5, 301), metavar="5–300")
    args = parser.parse_args()
    url = os.getenv("VALHALLA_LOKI_QUEUE_URL", "").rstrip("/")
    key = os.getenv("VALHALLA_LOKI_REVIEWER_KEY", "")
    reviewer_id = os.getenv("VALHALLA_LOKI_REVIEWER_ID", "").strip()
    parsed = urlsplit(url)
    if (os.getenv("VALHALLA_LOKI_ANALYST_ENABLED") != "1" or not key or not 1 <= len(reviewer_id) <= 100 or parsed.scheme != "https"
            or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment):
        parser.exit(2, "Loki analyst disabled or queue configuration invalid.\n")
    run_id = str(uuid4())

    def emit(line):
        evidence = json.loads(line)
        evidence.update(run_id=run_id, artifact_type=args.artifact_type,
                        observed_at=datetime.now(timezone.utc).isoformat())
        print(json.dumps(evidence, sort_keys=True), flush=True)

    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    with httpx.Client(base_url=url, headers={"X-Loki-Reviewer-Key": key}, timeout=15,
                      follow_redirects=False, trust_env=False) as client:
        return poll(lambda: tick(client, args.artifact_type, reviewer_id), stop, args.poll_seconds, emit=emit, once=args.once)


if __name__ == "__main__":
    raise SystemExit(main())
