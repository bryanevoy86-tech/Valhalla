#!/usr/bin/env python3
"""Poll approved Builder assignments and submit isolated test receipts."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
from urllib.parse import urlsplit
from uuid import UUID

from builder_test_review import test_review

CRON_ROOT = Path(__file__).resolve().parents[1] / "services" / "api" / "tools" / "cron"
sys.path.insert(0, str(CRON_ROOT))
from business_factory_worker import poll


def tick(client, repository, image, *, runner=test_review):
    queued = client.post("/builder/assignments/claim")
    queued.raise_for_status()
    job = queued.json()
    if job["status"] != "leased":
        return {"status": job["status"]}
    assignment_id = UUID(job["assignment_id"])
    # The worker never pulls a requested image or fetches an untrusted checkout.
    if job["image_id"] != image:
        result = None
    else:
        try:
            result = runner(job["review"], repository, job["base_commit"], image, 180)
        except (ValueError, TypeError, SyntaxError, OSError, subprocess.SubprocessError):
            result = None
    if result is None:
        result = {
            "status": "sandbox_unavailable", "exit_code": None, "suite": "services/api/tests",
            "base_commit": job["base_commit"], "image_id": job["image_id"], "bundle_sha256": job["bundle_sha256"],
            "source_modified": False, "committed": False, "deployed": False, "release_authorized": False,
        }
    submitted = client.post(f"/builder/assignments/{assignment_id}/receipt", json={
        **result, "lease_id": job["lease_id"],
    })
    submitted.raise_for_status()
    return {"status": submitted.json()["status"], "release_authorized": False}


def main():
    import httpx

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--image-id", required=True)
    args = parser.parse_args()
    url = os.getenv("VALHALLA_BUILDER_QUEUE_URL", "").rstrip("/")
    key = os.getenv("VALHALLA_BUILDER_RUNNER_KEY", "")
    parsed = urlsplit(url)
    if (os.getenv("VALHALLA_BUILDER_ASSIGNMENT_ENABLED") != "1" or not key or parsed.scheme != "https"
            or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment
            or not re.fullmatch(r"sha256:[a-f0-9]{64}", args.image_id)):
        parser.exit(2, "Builder runner disabled or staging configuration invalid.\n")
    stop = threading.Event()
    with httpx.Client(base_url=url, headers={"X-Builder-Runner-Key": key}, timeout=15,
                      follow_redirects=False, trust_env=False) as client:
        try:
            return poll(lambda: tick(client, args.repository, args.image_id), stop, once=args.once)
        except KeyboardInterrupt:
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
