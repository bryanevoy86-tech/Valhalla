from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.dependencies import require_builder_key
from ..models.research import Playbook
from ..schemas.research import PlaybookIn, PlaybookOut

router = APIRouter(prefix="/playbooks", tags=["playbooks"])


@router.get("", response_model=List[PlaybookOut])
def list_playbooks(db: Session = Depends(get_db)):
    """List all playbooks (no auth required for reading)"""
    playbooks = db.query(Playbook).filter(Playbook.enabled == True).order_by(Playbook.slug).all()
    return playbooks


@router.get("/{slug}", response_model=PlaybookOut)
def get_playbook(slug: str, db: Session = Depends(get_db)):
    """Get a specific playbook by slug"""
    playbook = db.query(Playbook).filter(Playbook.slug == slug, Playbook.enabled == True).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return playbook


@router.post("", response_model=PlaybookOut)
def create_playbook(payload: PlaybookIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    """Create a new playbook (requires API key)"""
    # Check if slug already exists
    existing = db.query(Playbook).filter(Playbook.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Playbook with slug '{payload.slug}' already exists")
    
    playbook = Playbook(
        slug=payload.slug,
        title=payload.title,
        body_md=payload.body_md,
        tags=payload.tags,
        enabled=payload.enabled,
    )
    db.add(playbook)
    db.commit()
    db.refresh(playbook)
    return playbook


@router.put("/{slug}", response_model=PlaybookOut)
def update_playbook(slug: str, payload: PlaybookIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    """Update an existing playbook"""
    playbook = db.query(Playbook).filter(Playbook.slug == slug).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    playbook.title = payload.title
    playbook.body_md = payload.body_md
    playbook.tags = payload.tags
    playbook.enabled = payload.enabled
    playbook.updated_at = datetime.utcnow()
    
    db.add(playbook)
    db.commit()
    db.refresh(playbook)
    return playbook


@router.delete("/{slug}")
def delete_playbook(slug: str, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    """Delete a playbook"""
    playbook = db.query(Playbook).filter(Playbook.slug == slug).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    db.delete(playbook)
    db.commit()
    return {"ok": True, "message": f"Playbook '{slug}' deleted"}
