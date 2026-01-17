"""
PACK AV: Narrative Story Mode Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.story_mode import StoryPrompt, StoryOutput
from app.schemas.story_mode import StoryPromptCreate, StoryOutputCreate


def create_prompt(db: Session, payload: StoryPromptCreate) -> StoryPrompt:
    obj = StoryPrompt(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_prompts(
    db: Session,
    audience: Optional[str] = None,
    theme: Optional[str] = None,
    limit: int = 100,
) -> List[StoryPrompt]:
    q = db.query(StoryPrompt)
    if audience:
        q = q.filter(StoryPrompt.audience == audience)
    if theme:
        q = q.filter(StoryPrompt.theme == theme)
    return q.order_by(StoryPrompt.created_at.desc()).limit(limit).all()


def create_story_output(db: Session, payload: StoryOutputCreate) -> StoryOutput:
    obj = StoryOutput(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_story_outputs(
    db: Session,
    audience: Optional[str] = None,
    theme: Optional[str] = None,
    limit: int = 100,
) -> List[StoryOutput]:
    q = db.query(StoryOutput)
    if audience:
        q = q.filter(StoryOutput.audience == audience)
    if theme:
        q = q.filter(StoryOutput.theme == theme)
    return q.order_by(StoryOutput.created_at.desc()).limit(limit).all()
