from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.lease import Lease
from app.schemas.tenant_lease import LeaseCreate, LeaseOut

router = APIRouter()


@router.post("/", response_model=LeaseOut)
def create_lease(payload: LeaseCreate, db: Session = Depends(get_db)):
    obj = Lease(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[LeaseOut])
def list_leases(
    rental_property_id: int | None = None,
    tenant_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Lease)
    if rental_property_id is not None:
        query = query.filter(Lease.rental_property_id == rental_property_id)
    if tenant_id is not None:
        query = query.filter(Lease.tenant_id == tenant_id)
    if status:
        query = query.filter(Lease.status == status)
    return query.all()
