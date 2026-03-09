from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.tenant import Tenant
from app.schemas.tenant_lease import TenantCreate, TenantOut

router = APIRouter()


@router.post("/", response_model=TenantOut)
def create_tenant(payload: TenantCreate, db: Session = Depends(get_db)):
    obj = Tenant(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[TenantOut])
def list_tenants(active: bool | None = None, db: Session = Depends(get_db)):
    query = db.query(Tenant)
    if active is not None:
        query = query.filter(Tenant.active == active)
    return query.all()
