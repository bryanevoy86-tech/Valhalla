from sqlalchemy.orm import Session

from ..models.buyer import Buyer
from ..schemas.buyer import BuyerCreate
from ..services import audit


def create(db: Session, data: BuyerCreate) -> Buyer:
    obj = Buyer(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    audit.log(
        db,
        actor_id=0,
        action="buyer_create",
        entity="buyer",
        entity_id=obj.id,
        extra={"legacy_id": obj.legacy_id},
    )
    return obj


def list_all(
    db: Session, limit: int = 100, offset: int = 0, legacy_id: str | None = None
) -> list[Buyer]:
    q = db.query(Buyer).filter(Buyer.active == True)
    if legacy_id:
        q = q.filter(Buyer.legacy_id == legacy_id)
    return q.order_by(Buyer.id.desc()).offset(offset).limit(limit).all()
