"""
PACK AA: Story Engine Router
Prefix: /stories
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.story_engine import (
    StoryTemplateCreate,
    StoryTemplateUpdate,
    StoryTemplateOut,
    StoryEpisodeCreate,
    StoryEpisodeOut,
)
from app.services.story_engine import (
    create_template,
    update_template,
    get_template,
    list_templates,
    create_episode,
    list_episodes_for_child,
)

router = APIRouter(prefix="/stories", tags=["Stories"])


@router.post("/templates", response_model=StoryTemplateOut)
def create_story_template(
    payload: StoryTemplateCreate,
    db: Session = Depends(get_db),
):
    """Create a new story template."""
    return create_template(db, payload)


@router.get("/templates", response_model=List[StoryTemplateOut])
def list_story_templates(
    arc_name: Optional[str] = Query(None),
    purpose: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List story templates with optional filtering by arc name or purpose."""
    return list_templates(db, arc_name=arc_name, purpose=purpose)


@router.get("/templates/{template_id}", response_model=StoryTemplateOut)
def get_story_template(
    template_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific story template by ID."""
    obj = get_template(db, template_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Template not found")
    return obj


@router.patch("/templates/{template_id}", response_model=StoryTemplateOut)
def update_story_template(
    template_id: int,
    payload: StoryTemplateUpdate,
    db: Session = Depends(get_db),
):
    """Update a story template."""
    obj = update_template(db, template_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Template not found")
    return obj


@router.post("/episodes", response_model=StoryEpisodeOut)
def create_story_episode(
    payload: StoryEpisodeCreate,
    db: Session = Depends(get_db),
):
    """Create a new story episode (concrete instance of a template)."""
    return create_episode(db, payload)


@router.get("/episodes/by-child/{child_id}", response_model=List[StoryEpisodeOut])
def list_episodes_child(
    child_id: int,
    db: Session = Depends(get_db),
):
    """List all episodes told to a specific child."""
    return list_episodes_for_child(db, child_id)
