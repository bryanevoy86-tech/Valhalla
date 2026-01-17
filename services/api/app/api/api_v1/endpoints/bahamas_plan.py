from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.bahamas_plan import BahamasPlan
from app.schemas.bahamas_plan import (
    BahamasPlanCreate,
    BahamasPlanUpdate,
    BahamasPlanOut,
)

router = APIRouter()


@router.post("/", response_model=BahamasPlanOut)
def create_bahamas_plan(
    payload: BahamasPlanCreate,
    db: Session = Depends(get_db),
):
    obj = BahamasPlan(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[BahamasPlanOut])
def list_bahamas_plans(db: Session = Depends(get_db)):
    return db.query(BahamasPlan).all()


@router.put("/{plan_id}", response_model=BahamasPlanOut)
def update_bahamas_plan(
    plan_id: int,
    payload: BahamasPlanUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(BahamasPlan).get(plan_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
