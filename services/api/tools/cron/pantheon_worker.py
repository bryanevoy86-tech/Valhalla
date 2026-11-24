#!/usr/bin/env python3
"""Opt-in PostgreSQL process for one independently scheduled Pantheon role."""
import argparse
import os
import signal
import threading

from business_factory_worker import configuration_ready, poll


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    from app.pantheon.roles import ROLES
    parser.add_argument("--role", required=True, choices=ROLES)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, choices=range(5, 301), default=15, metavar="5–300")
    args = parser.parse_args()
    if not configuration_ready({
        "VALHALLA_INTERNAL_FACTORY_WORKER_ENABLED": os.getenv("VALHALLA_PANTHEON_WORKER_ENABLED"),
        "DATABASE_URL": os.getenv("DATABASE_URL"),
    }):
        parser.exit(2, "Specialist worker disabled or explicit PostgreSQL configuration missing.\n")

    from app.core.db import SessionLocal
    from app.pantheon.monitor import run_scheduled_assignment

    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())

    def tick() -> dict:
        with SessionLocal.session_factory() as db:
            return run_scheduled_assignment(db, args.role)

    return poll(tick, stop, args.poll_seconds, once=args.once)


if __name__ == "__main__":
    raise SystemExit(main())
