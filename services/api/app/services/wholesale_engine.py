"""
PACK X: Wholesaling Engine Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.wholesale import WholesalePipeline, WholesaleActivityLog
from app.schemas.wholesale import (
    WholesalePipelineCreate,
    WholesalePipelineUpdate,
    WholesaleActivityLogIn,
)


def create_pipeline(db: Session, payload: WholesalePipelineCreate) -> WholesalePipeline:
    obj = WholesalePipeline(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_pipeline(
    db: Session,
    pipeline_id: int,
    payload: WholesalePipelineUpdate,
) -> Optional[WholesalePipeline]:
    obj = db.query(WholesalePipeline).filter(WholesalePipeline.id == pipeline_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def get_pipeline(db: Session, pipeline_id: int) -> Optional[WholesalePipeline]:
    return db.query(WholesalePipeline).filter(WholesalePipeline.id == pipeline_id).first()


def list_pipelines(
    db: Session,
    stage: Optional[str] = None,
) -> List[WholesalePipeline]:
    q = db.query(WholesalePipeline)
    if stage:
        q = q.filter(WholesalePipeline.stage == stage)
    return q.order_by(WholesalePipeline.created_at.desc()).all()


def log_activity(
    db: Session,
    pipeline_id: int,
    payload: WholesaleActivityLogIn,
) -> Optional[WholesaleActivityLog]:
    pipe = get_pipeline(db, pipeline_id)
    if not pipe:
        return None

    act = WholesaleActivityLog(
        pipeline_id=pipeline_id,
        **payload.model_dump(),
    )
    db.add(act)
    db.commit()
    db.refresh(act)
    return act
