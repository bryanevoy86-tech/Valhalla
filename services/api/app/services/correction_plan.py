"""
PACK CL14: Correction Plan Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.correction_plan import CorrectionPlan
from app.schemas.correction_plan import CorrectionPlanCreate


def create_plan(db: Session, payload: CorrectionPlanCreate) -> CorrectionPlan:
    obj = CorrectionPlan(
        plan_id=payload.plan_id,
        run_id=payload.run_id,
        title=payload.title,
        description=payload.description,
        actions=payload.actions,
        requires_human_approval=payload.requires_human_approval,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_plans(db: Session, status: Optional[str] = None, limit: int = 200) -> List[CorrectionPlan]:
    q = db.query(CorrectionPlan).order_by(CorrectionPlan.id.desc())
    if status:
        q = q.filter(CorrectionPlan.status == status)
    return q.limit(limit).all()
