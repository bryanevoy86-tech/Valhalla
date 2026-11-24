#!/usr/bin/env python3
"""Poll one authorized local Foundry operating rehearsal."""
import argparse
import os
import signal
import threading
from uuid import UUID

import httpx

from business_factory_worker import poll


def tick(client, run_id):
    reply = client.post(f"/api/foundry/operating-rehearsal/{run_id}/advance")
    if reply.status_code in (409, 503):
        return {"status": "blocked", "http_status": reply.status_code, "emergency_stop": reply.status_code == 503}
    reply.raise_for_status()
    data = reply.json()
    if data.get("status") == "waiting":
        return {"status": "waiting", "reason": data["reason"]}
    receipt = data.get("receipt", {})
    if (data.get("status") not in {"advanced", "completed"} or receipt.get("actor") != "PRIME_WORKER"
            or receipt.get("external_effects") != 0 or not receipt.get("sha256")):
        raise RuntimeError("Operating rehearsal did not return a worker receipt")
    return {"status": data["status"], "phase": receipt["phase"], "receipt_sha256": receipt["sha256"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, required=True, choices=range(1024, 65536), metavar="PORT")
    parser.add_argument("--run-id", type=UUID, required=True)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    key = os.environ.get("VALHALLA_PRIME_CONTROL_KEY")
    if os.getenv("VALHALLA_FOUNDRY_OPERATING_REHEARSAL") != "1" or not key:
        parser.exit(2, "Operating rehearsal disabled or Prime credential absent.\n")
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    # The worker never receives a fixture provider signature or buyer token.
    with httpx.Client(base_url=f"http://127.0.0.1:{args.port}", headers={"X-Prime-Control-Key": key},
                      timeout=10, trust_env=False, follow_redirects=False) as client:
        def run():
            result = tick(client, args.run_id)
            if result["status"] == "completed":
                stop.set()
            return result

        return poll(run, stop, once=args.once)


if __name__ == "__main__":
    raise SystemExit(main())
