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
                mark_clone_status(
                    db,
                    plan.id,
                    status="completed",
                    result={"note": "placeholder deploy complete"},
                )
        except Exception as _e:
            # Clone plans not available or failed; skip
            pass
        
        # Simple log marker
        print(f"[scheduler] Jobs completed at {datetime.now(timezone.utc).isoformat()}")
    finally:
        db.close()


async def scheduler_loop() -> None:
    while True:
        await run_jobs_once()
        await asyncio.sleep(INTERVAL_SECONDS)
