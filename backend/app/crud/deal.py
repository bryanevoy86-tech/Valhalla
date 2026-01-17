from sqlalchemy.orm import Session

from ..models.deal import Deal
from ..schemas.deal import DealCreate
from ..services import audit


def create(db: Session, data: DealCreate) -> Deal:
    obj = Deal(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    audit.log(
        db,
        actor_id=0,
        action="deal_create",
        entity="deal",
        entity_id=obj.id,
        extra={"legacy_id": obj.legacy_id, "arv": obj.arv, "mao": obj.mao},
    )
    return obj
