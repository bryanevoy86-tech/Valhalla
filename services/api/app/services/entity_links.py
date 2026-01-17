"""
PACK AW: Crosslink / Relationship Graph Service
"""

from typing import List
from sqlalchemy.orm import Session

from app.models.entity_links import EntityLink
from app.schemas.entity_links import EntityLinkCreate


def create_link(db: Session, payload: EntityLinkCreate) -> EntityLink:
    obj = EntityLink(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_links_from(
    db: Session,
    from_type: str,
    from_id: str,
) -> List[EntityLink]:
    return (
        db.query(EntityLink)
        .filter(
            EntityLink.from_type == from_type,
            EntityLink.from_id == from_id,
        )
        .order_by(EntityLink.created_at.desc())
        .all()
    )


def list_links_to(
    db: Session,
    to_type: str,
    to_id: str,
) -> List[EntityLink]:
    return (
        db.query(EntityLink)
        .filter(
            EntityLink.to_type == to_type,
            EntityLink.to_id == to_id,
        )
        .order_by(EntityLink.created_at.desc())
        .all()
    )
