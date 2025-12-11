"""SaaS Manager Service Layer"""
from sqlalchemy.orm import Session
from . import models, schemas


def create_tenant(db: Session, data: schemas.TenantCreate) -> models.Tenant:
    """Create a new multi-tenant account."""
    t = models.Tenant(**data.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def list_tenants(db: Session):
    """List all tenants, ordered by creation date."""
    return db.query(models.Tenant).order_by(models.Tenant.created_at.desc()).all()


def get_tenant(db: Session, tenant_id):
    """Get a specific tenant by ID."""
    return db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()


def update_tenant(db: Session, tenant: models.Tenant, data: schemas.TenantUpdate):
    """Update a tenant's plan, status, or usage."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tenant, field, value)
    db.commit()
    db.refresh(tenant)
    return tenant
