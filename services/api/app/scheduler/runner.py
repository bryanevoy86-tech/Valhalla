"""Periodic maintenance, with no implied deployment success."""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.freeze.service import list_events as freeze_list_events
from app.audit.service import list_events as audit_list_events
from app.knowledge.service import purge_expired as knowledge_purge

logger = logging.getLogger(__name__)
INTERVAL_SECONDS = 300


async def run_jobs_once() -> None:
    db: Session = SessionLocal()
    try:
        for name, action in (
            ("freeze_list_events", freeze_list_events),
            ("audit_list_events", audit_list_events),
            ("knowledge_purge", knowledge_purge),
        ):
            try:
                action(db)
            except Exception:
                db.rollback()
                logger.exception("Scheduler maintenance step failed: %s", name)

        # A queued clone is NOT a completed deployment. Until an actual
        # provisioning executor confirms the result, preserve the queued state.
        try:
            from app.orchestrator.models import ClonePlan

            queued_count = db.query(ClonePlan).filter(ClonePlan.status == "queued").count()
            if queued_count:
                logger.warning(
                    "%d clone plan(s) remain queued: no verified clone deployment performed",
                    queued_count,
                )
        except Exception:
            db.rollback()
            logger.exception("Unable to inspect queued clone plans")

        # Run arbitrage maintenance independently of clone queue health.
        try:
            from app.arbitrage.service import bootstrap_safe_rules, evaluate_and_record_metrics

            from app.services.prime_business_execution import _emergency_stop_active

            if not _emergency_stop_active(db):
                bootstrap_safe_rules(db)
                evaluate_and_record_metrics(db)
        except Exception:
            db.rollback()
            logger.exception("Arbitrage maintenance step failed")

        logger.info("Scheduler maintenance pass ended at %s", datetime.now(timezone.utc).isoformat())
    finally:
        db.close()


async def scheduler_loop() -> None:
    while True:
        await run_jobs_once()
        await asyncio.sleep(INTERVAL_SECONDS)
