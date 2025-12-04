from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.whole_life_policy import WholeLifePolicy
from app.schemas.whole_life_policy import (
    WholeLifePolicyCreate,
    WholeLifePolicyUpdate,
    WholeLifePolicyOut,
)

router = APIRouter()


@router.post("/", response_model=WholeLifePolicyOut)
def create_whole_life_policy(payload: WholeLifePolicyCreate, db: Session = Depends(get_db)):
    obj = WholeLifePolicy(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[WholeLifePolicyOut])
def list_whole_life_policies(
    owner_entity: str | None = None,
    insured_name: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(WholeLifePolicy)
    if owner_entity:
        query = query.filter(WholeLifePolicy.owner_entity == owner_entity)
    if insured_name:
        query = query.filter(WholeLifePolicy.insured_name == insured_name)
    return query.all()


@router.put("/{policy_id}", response_model=WholeLifePolicyOut)
def update_whole_life_policy(policy_id: int, payload: WholeLifePolicyUpdate, db: Session = Depends(get_db)):
    obj = db.query(WholeLifePolicy).get(policy_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
