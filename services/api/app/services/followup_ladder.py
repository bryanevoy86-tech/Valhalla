from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.models.followup_task import FollowupTask
from app.services.kpi import emit_kpi


DEFAULT_LADDER = [
    # step, delay minutes, channel
    (1, 0, "SMS"),
    (2, 30, "CALL"),
    (3, 180, "SMS"),
    (4, 1440, "CALL"),   # next day
    (5, 4320, "SMS"),    # 3 days
    (6, 10080, "CALL"),  # 7 days
]


def create_ladder(db: Session, lead_id: str | None, province: str | None, market: str | None, owner: str | None, correlation_id: str | None) -> List[FollowupTask]:
    now = datetime.utcnow()
    tasks: List[FollowupTask] = []
    for step, delay_min, channel in DEFAULT_LADDER:
        t = FollowupTask(
            lead_id=lead_id,
            province=(province or "").upper() or None,
            market=(market or "").upper() or None,
            channel=channel,
            step=step,
            due_at=now + timedelta(minutes=delay_min),
            owner=owner,
            correlation_id=correlation_id,
        )
        db.add(t)
        tasks.append(t)
    db.commit()
    for t in tasks:
        db.refresh(t)

    emit_kpi(db, "WHOLESALE", "ladder_created", success=True, actor=owner, correlation_id=correlation_id, detail={"tasks": len(tasks)})
    return tasks


def complete_task(db: Session, task_id: int, actor: str | None, correlation_id: str | None) -> FollowupTask:
    t = db.query(FollowupTask).filter(FollowupTask.id == task_id).first()
    if not t:
        raise ValueError("Task not found")
    t.completed = True
    t.completed_at = datetime.utcnow()
    db.add(t)
    db.commit()
    db.refresh(t)

    emit_kpi(db, "WHOLESALE", "followup_completed", success=True, actor=actor, correlation_id=correlation_id, detail={"task_id": task_id, "step": t.step, "channel": t.channel})
    return t


def due_tasks(db: Session, limit: int = 50) -> List[FollowupTask]:
    now = datetime.utcnow()
    return db.query(FollowupTask).filter(FollowupTask.completed == False, FollowupTask.due_at <= now).order_by(FollowupTask.due_at.asc()).limit(limit).all()


def sla_snapshot(db: Session) -> Dict[str, Any]:
    """
    SLA metric: percent of tasks completed within X minutes of due time.
    """
    rows = db.query(FollowupTask).filter(FollowupTask.completed == True).order_by(FollowupTask.completed_at.desc()).limit(500).all()
    if not rows:
        return {"count": 0, "within_30m": None, "within_2h": None}

    within_30 = 0
    within_120 = 0
    for r in rows:
        if not r.completed_at:
            continue
        delta_min = (r.completed_at - r.due_at).total_seconds() / 60.0
        if delta_min <= 30:
            within_30 += 1
        if delta_min <= 120:
            within_120 += 1

    n = len(rows)
    return {"count": n, "within_30m": within_30 / n, "within_2h": within_120 / n}
