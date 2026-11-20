#!/usr/bin/env python3
"""Opt-in internal-only Factory polling process; no external provider effects.

No process is started by importing this module. Deployment and database
selection must be separately approved. Run from services/api as:
  python tools/cron/business_factory_worker.py --once
  python tools/cron/business_factory_worker.py --poll-seconds 15
Both require explicit configuration. This is NOT a general leased worker.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
import signal
import sys
import threading
from typing import Callable

API_ROOT = Path(__file__).resolve().parents[2]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


def tick(session_factory: Callable, execute: Callable, check_schema: Callable) -> dict:
    """Own exactly one fresh session and expose only non-sensitive results."""
    with session_factory() as db:
        try:
            check_schema(db)
            result = execute(db)
            if not isinstance(result, dict):
                raise RuntimeError("invalid worker result")
            state = result.get("status")
            if state == "completed":
                evidence = result.get("receipt")
                if (result.get("verified") is not True or not isinstance(evidence, dict)
                        or type(evidence.get("external_effects")) is not int
                        or evidence["external_effects"] != 0
                        or evidence.get("artifact_type") != "product_listing_draft"
                        or type(evidence.get("media_content_id")) is not int
                        or evidence["media_content_id"] <= 0
                        or not isinstance(evidence.get("action_id"), str)
                        or not re.fullmatch(r"bfd_[0-9a-f]{32}", evidence["action_id"])
                        or not isinstance(evidence.get("sha256"), str)
                        or not re.fullmatch(r"[0-9a-f]{64}", evidence["sha256"])
                        or evidence.get("sales_verified") is not False
                        or evidence.get("verification_scope") != "database_artifact_only"):
                    raise RuntimeError("worker completion has invalid internal evidence")
                return {"status": "internal_artifact_verified", "verified": True}
            if state in {"idle", "blocked"} and result.get("verified") is False:
                return {"status": state, "verified": False,
                        "emergency_stop": result.get("reason") == "EMERGENCY_STOP_ACTIVE"}
            raise RuntimeError("unverified worker result")
        except Exception:
            db.rollback()
            raise


def poll(run_tick: Callable, stop: threading.Event, interval: int = 15,
         emit: Callable = print, once: bool = False) -> int:
    if not 5 <= interval <= 300:
        raise ValueError("poll seconds outside supported limits")
    failures = 0
    while not stop.is_set():
        try:
            result = run_tick()
            failures = 0
            emit(json.dumps(result, sort_keys=True))
            if once:
                return 2 if result.get("status") == "blocked" else 0
            delay = max(interval, 60) if result.get("emergency_stop") else interval
        except Exception as exc:
            failures += 1
            # No exception text, SQL, credentials, or customer data in logs.
            emit(json.dumps({"status": "retry_pending", "verified": False,
                             "error_type": type(exc).__name__}, sort_keys=True))
            if once:
                return 2
            delay = min(300, interval * (2 ** min(failures, 5)))
        stop.wait(delay)
    return 0


def configuration_ready(env: dict) -> bool:
    from urllib.parse import urlsplit
    if env.get("VALHALLA_INTERNAL_FACTORY_WORKER_ENABLED") != "1":
        return False
    # Force explicit durable DB configuration; never use silent SQLite or
    # .env fallback. Actual identity and migration checks are release gates.
    try:
        parts = urlsplit(env.get("DATABASE_URL", ""))
        return (parts.scheme in {"postgresql", "postgresql+psycopg2", "postgresql+psycopg"}
                and bool(parts.hostname) and bool(parts.path.strip("/")))
    except (TypeError, ValueError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=15)
    args = parser.parse_args()
    if not configuration_ready(os.environ):
        parser.exit(2, "Internal Factory worker disabled or explicit PostgreSQL configuration missing.\n")
    if not 5 <= args.poll_seconds <= 300:
        parser.error("poll seconds must be 5–300")
    from app.core.db import SessionLocal
    from app.routers.prime_business_factory import require_factory_schema
    from app.services.prime_business_execution import run_one_approved_draft
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    return poll(lambda: tick(SessionLocal.session_factory, run_one_approved_draft, require_factory_schema),
                stop, args.poll_seconds, once=args.once)


if __name__ == "__main__":
    raise SystemExit(main())
