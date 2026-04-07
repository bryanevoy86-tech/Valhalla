"""
PACK AW: Crosslink / Relationship Graph Router
Prefix: /links
"""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.entity_links import EntityLinkCreate, EntityLinkOut
from app.services.entity_links import create_link, list_links_from, list_links_to

router = APIRouter(prefix="/links", tags=["EntityLinks"])


@router.post("/", response_model=EntityLinkOut)
def create_link_endpoint(
    payload: EntityLinkCreate,
    db: Session = Depends(get_db),
):
    """Create a new entity relationship link."""
    return create_link(db, payload)


@router.get("/from", response_model=List[EntityLinkOut])
def list_links_from_endpoint(
    from_type: str = Query(...),
    from_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """List all outgoing links from an entity."""
    return list_links_from(db, from_type=from_type, from_id=from_id)


@router.get("/to", response_model=List[EntityLinkOut])
def list_links_to_endpoint(
    to_type: str = Query(...),
    to_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """List all incoming links to an entity."""
    return list_links_to(db, to_type=to_type, to_id=to_id)
