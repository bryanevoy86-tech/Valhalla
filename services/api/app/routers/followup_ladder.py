from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.followup_task import FollowupTask
from app.services.followup_ladder import create_ladder, complete_task, due_tasks, sla_snapshot

router = APIRouter(prefix="/followups", tags=["Followups", "Ladder"])


@router.post("/ladder/create")
def ladder_create(lead_id: str | None = None, province: str | None = None, market: str | None = None, owner: str | None = None, correlation_id: str | None = None, db: Session = Depends(get_db)):
    tasks = create_ladder(db, lead_id, province, market, owner, correlation_id)
    return {"ok": True, "tasks": [{"id": t.id, "due_at": t.due_at, "channel": t.channel, "step": t.step} for t in tasks]}


@router.post("/task/{task_id}/complete")
def task_complete(task_id: int, actor: str | None = None, correlation_id: str | None = None, db: Session = Depends(get_db)):
    t = complete_task(db, task_id, actor, correlation_id)
    return {"ok": True, "task": {"id": t.id, "completed_at": t.completed_at, "step": t.step, "channel": t.channel}}


@router.get("/due")
def due(limit: int = 50, db: Session = Depends(get_db)):
    rows = due_tasks(db, limit=limit)
    return {"ok": True, "due": [{"id": r.id, "lead_id": r.lead_id, "due_at": r.due_at, "channel": r.channel, "step": r.step, "owner": r.owner} for r in rows]}


@router.get("/sla")
def sla(db: Session = Depends(get_db)):
    return {"ok": True, "sla": sla_snapshot(db)}
