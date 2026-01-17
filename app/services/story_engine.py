"""
PACK AA: Story Engine Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.story_engine import StoryTemplate, StoryEpisode
from app.schemas.story_engine import (
    StoryTemplateCreate,
    StoryTemplateUpdate,
    StoryEpisodeCreate,
)


def create_template(db: Session, payload: StoryTemplateCreate) -> StoryTemplate:
    obj = StoryTemplate(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_template(
    db: Session,
    template_id: int,
    payload: StoryTemplateUpdate,
) -> Optional[StoryTemplate]:
    obj = db.query(StoryTemplate).filter(StoryTemplate.id == template_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def get_template(db: Session, template_id: int) -> Optional[StoryTemplate]:
    return db.query(StoryTemplate).filter(StoryTemplate.id == template_id).first()


def list_templates(
    db: Session,
    arc_name: Optional[str] = None,
    purpose: Optional[str] = None,
) -> List[StoryTemplate]:
    q = db.query(StoryTemplate).filter(StoryTemplate.is_active.is_(True))
    if arc_name:
        q = q.filter(StoryTemplate.arc_name == arc_name)
    if purpose:
        q = q.filter(StoryTemplate.purpose == purpose)
    return q.order_by(StoryTemplate.created_at.desc()).all()


def create_episode(db: Session, payload: StoryEpisodeCreate) -> StoryEpisode:
    obj = StoryEpisode(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_episodes_for_child(
    db: Session,
    child_id: int,
) -> List[StoryEpisode]:
    return (
        db.query(StoryEpisode)
        .filter(StoryEpisode.child_id == child_id)
        .order_by(StoryEpisode.created_at.desc())
        .all()
    )
