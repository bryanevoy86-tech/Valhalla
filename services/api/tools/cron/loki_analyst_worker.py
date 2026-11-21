#!/usr/bin/env python3
"""Run the independent local Loki analyst against the restricted queue."""
import argparse
import os
import signal
import threading
from urllib.parse import urlsplit
from uuid import UUID

import httpx

from business_factory_worker import poll
from app.loki.analyst import challenge


def tick(client: httpx.Client, kind: str) -> dict:
    response = client.get("/loki/worker/reviews", params={"limit": 1, "artifact_type": kind})
    response.raise_for_status()
    pending = response.json()
    if not pending:
        return {"status": "idle"}
    item = pending[0]
    review_id = UUID(item["review_id"])
    result = challenge(item)
    published = client.post(f"/loki/worker/reviews/{review_id}/result", json=result.model_dump(mode="json"))
    if published.status_code == 409:
        return {"status": "retry_pending", "verified": False}
    published.raise_for_status()
    receipt = published.json()
    if receipt.get("artifact_sha256") != result.artifact_sha256 or not receipt.get("result_sha256"):
        raise RuntimeError("Loki publication receipt is incomplete")
    return {"status": "reviewed", "findings": len(result.findings)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-type", default="universal_opportunity", choices=("universal_opportunity", "pantheon_report"))
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=15, choices=range(5, 301), metavar="5–300")
    args = parser.parse_args()
    url = os.getenv("VALHALLA_LOKI_QUEUE_URL", "").rstrip("/")
    key = os.getenv("VALHALLA_LOKI_REVIEWER_KEY", "")
    parsed = urlsplit(url)
    if (os.getenv("VALHALLA_LOKI_ANALYST_ENABLED") != "1" or not key or parsed.scheme != "https"
            or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment):
        parser.exit(2, "Loki analyst disabled or queue configuration invalid.\n")
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    with httpx.Client(base_url=url, headers={"X-Loki-Reviewer-Key": key}, timeout=15,
                      follow_redirects=False, trust_env=False) as client:
        return poll(lambda: tick(client, args.artifact_type), stop, args.poll_seconds, once=args.once)


if __name__ == "__main__":
    raise SystemExit(main())
