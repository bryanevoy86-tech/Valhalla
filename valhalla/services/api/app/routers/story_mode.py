"""
PACK AV: Narrative Story Mode Router
Prefix: /stories
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.story_mode import (
    StoryPromptCreate,
    StoryPromptOut,
    StoryOutputCreate,
    StoryOutputOut,
)
from app.services.story_mode import (
    create_prompt,
    list_prompts,
    create_story_output,
    list_story_outputs,
)

router = APIRouter(prefix="/stories", tags=["StoryMode"])


@router.post("/prompts", response_model=StoryPromptOut)
def create_prompt_endpoint(
    payload: StoryPromptCreate,
    db: Session = Depends(get_db),
):
    """Create a new story prompt."""
    return create_prompt(db, payload)


@router.get("/prompts", response_model=List[StoryPromptOut])
def list_prompts_endpoint(
    audience: Optional[str] = Query(None),
    theme: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List story prompts with optional filters."""
    return list_prompts(db, audience=audience, theme=theme, limit=limit)


@router.post("/outputs", response_model=StoryOutputOut)
def create_story_output_endpoint(
    payload: StoryOutputCreate,
    db: Session = Depends(get_db),
):
    """Create a new story output."""
    return create_story_output(db, payload)


@router.get("/outputs", response_model=List[StoryOutputOut])
def list_story_outputs_endpoint(
    audience: Optional[str] = Query(None),
    theme: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List story outputs with optional filters."""
    return list_story_outputs(db, audience=audience, theme=theme, limit=limit)
