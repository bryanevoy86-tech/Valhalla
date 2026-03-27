from sqlalchemy.orm import Session

from ..models.lead import Lead
from ..schemas.lead import LeadCreate
from ..services import audit
from ..services.tags import normalize_tags


def create(db: Session, data: LeadCreate, owner_id: int | None) -> Lead:
    payload = data.model_dump()
    payload["tags"] = normalize_tags(payload.get("tags"))
    obj = Lead(owner_id=owner_id, **payload)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    audit.log(
        db,
        actor_id=owner_id or 0,
        action="lead_create",
        entity="lead",
        entity_id=obj.id,
        extra={"name": obj.name, "legacy_id": obj.legacy_id},
    )
    return obj


def list_all(db: Session, limit: int = 100, offset: int = 0) -> list[Lead]:
    return db.query(Lead).order_by(Lead.id.desc()).offset(offset).limit(limit).all()


def list_all(db: Session, limit=100, offset=0):
    return db.query(Lead).order_by(Lead.id.desc()).offset(offset).limit(limit).all()
