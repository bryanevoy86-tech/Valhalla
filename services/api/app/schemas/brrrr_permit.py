"""PACK 72: BRRRR & Permit Schemas
Pydantic models for BRRRR analysis and permit validation.
"""

from pydantic import BaseModel
from typing import Optional


class BrrrrAnalysisBase(BaseModel):
    property_address: str
    blueprint_id: Optional[int] = None
    purchase_price: float
    rehab_cost: float
    arv_estimate: float
    rent_estimate: float
    refinance_ltv: float
    notes: Optional[str] = None


class BrrrrAnalysisCreate(BrrrrAnalysisBase):
    pass


class BrrrrAnalysisOut(BrrrrAnalysisBase):
    id: int

    class Config:
        from_attributes = True


class PermitPackageBase(BaseModel):
    brrrr_id: int
    jurisdiction: str
    package_payload: str
    status: str = "draft"


class PermitPackageCreate(PermitPackageBase):
    pass


class PermitPackageOut(PermitPackageBase):
    id: int

    class Config:
        from_attributes = True
