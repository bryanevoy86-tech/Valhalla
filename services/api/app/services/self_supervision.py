"""
PACK CL13: Self-Supervision Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.self_supervision import SelfSupervisionRun, SelfSupervisionFinding
from app.schemas.self_supervision import SelfSupervisionRunCreate


def create_run(db: Session, payload: SelfSupervisionRunCreate) -> SelfSupervisionRun:
    run = SelfSupervisionRun(
        run_id=payload.run_id,
        trigger=payload.trigger,
        scope=payload.scope,
        summary=payload.summary,
        metrics=payload.metrics,
    )
    db.add(run)
    db.flush()

    for f in payload.findings:
        finding = SelfSupervisionFinding(
            run_id=payload.run_id,
            finding_type=f.finding_type,
            severity=f.severity,
            title=f.title,
            detail=f.detail,
            context=f.context,
        )
        db.add(finding)

    db.commit()
    db.refresh(run)
    return run


def list_runs(db: Session, limit: int = 200) -> List[SelfSupervisionRun]:
    return (
        db.query(SelfSupervisionRun)
        .order_by(SelfSupervisionRun.id.desc())
        .limit(limit)
        .all()
    )


def list_findings(
    db: Session,
    run_id: Optional[str] = None,
    unresolved_only: bool = False,
    limit: int = 500,
) -> List[SelfSupervisionFinding]:
    q = db.query(SelfSupervisionFinding).order_by(SelfSupervisionFinding.id.desc())
    if run_id:
        q = q.filter(SelfSupervisionFinding.run_id == run_id)
    if unresolved_only:
        q = q.filter(SelfSupervisionFinding.resolved.is_(False))
    return q.limit(limit).all()
