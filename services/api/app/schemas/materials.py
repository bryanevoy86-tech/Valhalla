from pydantic import BaseModel
from typing import Optional

class MaterialItemBase(BaseModel):
    name: str
    category: Optional[str] = None
    unit: Optional[str] = "unit"
    preferred_supplier: Optional[str] = None
    last_price: float = 0.0
    currency: Optional[str] = "CAD"
    region: Optional[str] = None
    notes: Optional[str] = None

class MaterialItemCreate(MaterialItemBase):
    pass

class MaterialItemUpdate(BaseModel):
    category: Optional[str]
    unit: Optional[str]
    preferred_supplier: Optional[str]
    last_price: Optional[float]
    currency: Optional[str]
    region: Optional[str]
    notes: Optional[str]

class MaterialItemOut(MaterialItemBase):
    id: int

    class Config:
        orm_mode = True
