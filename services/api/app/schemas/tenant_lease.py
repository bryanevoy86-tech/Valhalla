from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class TenantBase(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    active: bool = True


class TenantCreate(TenantBase):
    pass


class TenantOut(TenantBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class LeaseBase(BaseModel):
    rental_property_id: int
    tenant_id: int
    start_date: datetime
    end_date: Optional[datetime] = None
    rent_amount: float
    rent_currency: str = "CAD"
    frequency: str = "monthly"
    deposit_amount: float = 0.0
    status: str = "active"


class LeaseCreate(LeaseBase):
    pass


class LeaseOut(LeaseBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class RentPaymentBase(BaseModel):
    lease_id: int
    due_date: datetime
    amount_due: float
    amount_paid: float = 0.0
    paid_date: Optional[datetime] = None
    status: str = "pending"
    method: Optional[str] = None


class RentPaymentCreate(RentPaymentBase):
    pass


class RentPaymentUpdate(BaseModel):
    amount_paid: Optional[float]
    paid_date: Optional[datetime]
    status: Optional[str]
    method: Optional[str]


class RentPaymentOut(RentPaymentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
