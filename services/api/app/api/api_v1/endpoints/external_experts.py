from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.external_expert import ExternalExpert
from app.schemas.external_expert import (
    ExternalExpertCreate,
    ExternalExpertUpdate,
    ExternalExpertOut,
)

router = APIRouter()


@router.post("/", response_model=ExternalExpertOut)
def create_external_expert(
    payload: ExternalExpertCreate,
    db: Session = Depends(get_db),
):
    obj = ExternalExpert(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[ExternalExpertOut])
def list_external_experts(
    specialty: str | None = None,
    jurisdiction: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ExternalExpert)
    if specialty:
        query = query.filter(ExternalExpert.specialty == specialty)
    if jurisdiction:
        query = query.filter(ExternalExpert.jurisdiction == jurisdiction)
    return query.order_by(ExternalExpert.preferred.desc()).all()


@router.put("/{expert_id}", response_model=ExternalExpertOut)
def update_external_expert(
    expert_id: int,
    payload: ExternalExpertUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(ExternalExpert).get(expert_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
