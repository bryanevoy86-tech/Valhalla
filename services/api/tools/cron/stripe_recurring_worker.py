#!/usr/bin/env python3
"""Opt-in durable subscriber invoice reconciliation without Stripe mutations."""
import argparse
import os
import signal
import threading

from business_factory_worker import configuration_ready, poll


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, choices=range(5, 301), default=30, metavar="5–300")
    args = parser.parse_args()
    if not configuration_ready({
        "VALHALLA_INTERNAL_FACTORY_WORKER_ENABLED": os.getenv("VALHALLA_STRIPE_RECURRING_WORKER_ENABLED"),
        "DATABASE_URL": os.getenv("DATABASE_URL"),
    }):
        parser.exit(2, "Stripe recurring worker disabled or explicit PostgreSQL configuration missing.\n")

    from app.core.db import SessionLocal
    from app.heimdall.authority import is_live
    from app.services.stripe_recurring import recurring_clients
    from app.services.stripe_recurring_worker import reconcile_due_invoice

    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())

    def tick():
        live = is_live()
        with SessionLocal.session_factory() as db, recurring_clients(live=live) as (reader, _):
            return reconcile_due_invoice(db, reader, live=live)

    return poll(tick, stop, args.poll_seconds, once=args.once)


if __name__ == "__main__":
    raise SystemExit(main())
