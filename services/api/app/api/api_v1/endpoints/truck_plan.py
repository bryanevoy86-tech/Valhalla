from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.truck_plan import TruckPlan
from app.schemas.truck_plan import (
    TruckPlanCreate,
    TruckPlanUpdate,
    TruckPlanOut,
)

router = APIRouter()


@router.post("/", response_model=TruckPlanOut)
def create_truck_plan(
    payload: TruckPlanCreate,
    db: Session = Depends(get_db),
):
    obj = TruckPlan(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[TruckPlanOut])
def list_truck_plans(db: Session = Depends(get_db)):
    return db.query(TruckPlan).all()


@router.put("/{plan_id}", response_model=TruckPlanOut)
def update_truck_plan(
    plan_id: int,
    payload: TruckPlanUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(TruckPlan).get(plan_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
