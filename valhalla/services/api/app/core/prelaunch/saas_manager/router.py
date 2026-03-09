"""SaaS Manager Router"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db

from . import schemas, service, models

router = APIRouter(prefix="/saas/tenants", tags=["saas"])


@router.get("/", response_model=List[schemas.TenantRead])
def list_all(db: Session = Depends(get_db)):
    """List all tenants."""
    tenants = service.list_tenants(db)
    return [schemas.TenantRead.model_validate(t) for t in tenants]


@router.post("/", response_model=schemas.TenantRead)
def create(payload: schemas.TenantCreate, db: Session = Depends(get_db)):
    """Create a new tenant account."""
    t = service.create_tenant(db, payload)
    return schemas.TenantRead.model_validate(t)


@router.patch("/{tenant_id}", response_model=schemas.TenantRead)
def update(
    tenant_id: UUID,
    payload: schemas.TenantUpdate,
    db: Session = Depends(get_db),
):
    """Update a tenant's settings."""
    t = service.get_tenant(db, tenant_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")

    updated = service.update_tenant(db, t, payload)
    return schemas.TenantRead.model_validate(updated)
