"""PACK 69: Code Compliance Schemas
Pydantic models for compliance check validation.
"""

from pydantic import BaseModel
from typing import Optional


class ComplianceCheckBase(BaseModel):
    blueprint_id: int
    region_code: str


class ComplianceCheckCreate(ComplianceCheckBase):
    pass


class ComplianceCheckOut(ComplianceCheckBase):
    id: int
    violations: Optional[str] = None
    passed: str

    class Config:
        from_attributes = True
