#!/usr/bin/env python3
"""Poll one explicitly approved disposable research round on loopback."""
import argparse
import os
import signal
import threading
from uuid import UUID

import httpx

from business_factory_worker import poll
# The shared worker import activates the API package path for the CLI.


def tick(client, round_id, scope):
    reply = client.post(f"/api/prime/customer-research/rehearsal/{round_id}/advance", json={"scope": scope})
    if reply.status_code in (409, 503):
        return {"status": "blocked", "verified": False, "emergency_stop": reply.status_code == 503}
    reply.raise_for_status()
    data = reply.json()
    if data.get("sent") is False and data.get("route") == "VOLUNTARY_INBOUND_FIXTURE":
        return {"status": "invitation_prepared", "sent": False}
    if data.get("status") in {"WAITING_FOR_VOLUNTARY_ANSWERS", "WAITING_FOR_INDEPENDENT_REVIEW"}:
        return {"status": data["status"]}
    if data.get("review_id") and data.get("evidence", {}).get("basis") == "DISPOSABLE_RESEARCH_FIXTURE":
        return {"status": "independent_review_queued", "artifact_sha256": data["artifact_sha256"]}
    if (data.get("decision") == "ABSTAIN_PENDING_GENUINE_EVIDENCE"
            and data.get("external_action_authorized") is False and data.get("independent_result_sha256")):
        return {"status": "abstained", "artifact_sha256": data["artifact_sha256"]}
    raise RuntimeError("Unrecognized research rehearsal result")


def main():
    from app.schemas.market_intelligence import MarketScope
    from app.services.customer_research import enabled

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000, choices=range(1024, 65536), metavar="PORT")
    parser.add_argument("--round-id", type=UUID, required=True)
    parser.add_argument("--scope", required=True, help="Approved round scope as JSON")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    key = os.environ.get("VALHALLA_PRIME_CONTROL_KEY")
    if not enabled() or not key:
        parser.exit(2, "Disposable research rehearsal disabled or Prime credential absent.\n")
    try:
        scope = MarketScope.model_validate_json(args.scope).model_dump()
    except ValueError:
        parser.error("Invalid research scope")
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    with httpx.Client(base_url=f"http://127.0.0.1:{args.port}", headers={"X-Prime-Control-Key": key},
                      follow_redirects=False, trust_env=False, timeout=10) as client:
        return poll(lambda: tick(client, args.round_id, scope), stop, once=args.once)


if __name__ == "__main__":
    main()
