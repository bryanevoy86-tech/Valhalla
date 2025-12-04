from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.brrrr_zone import BRRRRZone
from app.schemas.brrrr_zone import BRRRRZoneCreate, BRRRRZoneUpdate, BRRRRZoneOut

router = APIRouter()


@router.post("/", response_model=BRRRRZoneOut)
def create_brrrr_zone(payload: BRRRRZoneCreate, db: Session = Depends(get_db)):
    obj = BRRRRZone(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[BRRRRZoneOut])
def list_brrrr_zones(active: bool | None = None, db: Session = Depends(get_db)):
    query = db.query(BRRRRZone)
    if active is not None:
        query = query.filter(BRRRRZone.active == active)
    return query.all()


@router.put("/{zone_id}", response_model=BRRRRZoneOut)
def update_brrrr_zone(zone_id: int, payload: BRRRRZoneUpdate, db: Session = Depends(get_db)):
    obj = db.query(BRRRRZone).get(zone_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
