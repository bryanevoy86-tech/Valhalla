from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RentalPropertyBase(BaseModel):
    legacy_code: str
    zone_code: str
    name: str
    address_line1: str
    address_line2: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: str
    postal_code: Optional[str] = None
    property_type: Optional[str] = "single"
    bedrooms: int = 0
    bathrooms: float = 0.0
    square_feet: int = 0
    purchase_price: float = 0.0
    arv: float = 0.0
    current_value: float = 0.0
    status: Optional[str] = "acquisition"
    notes: Optional[str] = None


class RentalPropertyCreate(RentalPropertyBase):
    pass


class RentalPropertyUpdate(BaseModel):
    legacy_code: Optional[str]
    zone_code: Optional[str]
    name: Optional[str]
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    region: Optional[str]
    country: Optional[str]
    postal_code: Optional[str]
    property_type: Optional[str]
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    square_feet: Optional[int]
    purchase_price: Optional[float]
    arv: Optional[float]
    current_value: Optional[float]
    status: Optional[str]
    notes: Optional[str]


class RentalPropertyOut(RentalPropertyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
