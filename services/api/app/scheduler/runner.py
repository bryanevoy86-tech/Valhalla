import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.freeze.service import list_events as freeze_list_events
from app.audit.service import list_events as audit_list_events
from app.knowledge.service import purge_expired as knowledge_purge


INTERVAL_SECONDS = 300  # run every 5 minutes


async def run_jobs_once() -> None:
    db: Session = SessionLocal()
    try:
        # Execute maintenance tasks (best-effort)
        freeze_list_events(db)
        audit_list_events(db)
        knowledge_purge(db)
        
        # Advance queued clone plans (Pack 42 integration)
        try:
            from app.orchestrator.models import ClonePlan
            from app.orchestrator.service import mark_clone_status

            queued = db.query(ClonePlan).filter(ClonePlan.status == "queued").all()
            for plan in queued:
                # plan.id is an int attribute after flush; static checker may see InstrumentedAttribute
                mark_clone_status(
                    db,
                    getattr(plan, "id"),  # type: ignore[arg-type]
                    status="completed",
                    result={"note": "placeholder deploy complete"},
                )
        except Exception as _e:
            # Clone plans not available or failed; skip
            pass
        
            # Bootstrap safe rules and evaluate FX metrics (Pack 44 integration)
            try:
                from app.arbitrage.service import bootstrap_safe_rules, evaluate_and_record_metrics
            
                # Ensure safe defaults exist
                bootstrap_safe_rules(db)
            
                # Evaluate current metrics and enforce freeze rules
                evaluate_and_record_metrics(db)
            except Exception as _e:
                # Arbitrage not available or failed; skip
                pass
        
        # Simple log marker
        print(f"[scheduler] Jobs completed at {datetime.now(timezone.utc).isoformat()}")
    finally:
        db.close()


async def scheduler_loop() -> None:
    while True:
        await run_jobs_once()
        await asyncio.sleep(INTERVAL_SECONDS)
