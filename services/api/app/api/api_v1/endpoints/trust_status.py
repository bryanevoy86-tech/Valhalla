from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.trust_status import TrustStatus
from app.schemas.trust_status import (
    TrustStatusCreate,
    TrustStatusUpdate,
    TrustStatusOut,
)

router = APIRouter()


@router.post("/", response_model=TrustStatusOut)
def create_trust_status(
    payload: TrustStatusCreate,
    db: Session = Depends(get_db),
):
    obj = TrustStatus(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[TrustStatusOut])
def list_trust_status(
    status: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(TrustStatus)
    if status:
        query = query.filter(TrustStatus.status == status)
    return query.all()


@router.put("/{trust_id}", response_model=TrustStatusOut)
def update_trust_status(
    trust_id: int,
    payload: TrustStatusUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(TrustStatus).get(trust_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
