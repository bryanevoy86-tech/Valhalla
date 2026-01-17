"""PACK 64: Contract Engine Finalization Schemas
Pydantic models for contract template and record validation.
"""

from pydantic import BaseModel
from typing import Optional


class ContractTemplateBase(BaseModel):
    name: str
    version: str
    body: str


class ContractTemplateCreate(ContractTemplateBase):
    pass


class ContractTemplateOut(ContractTemplateBase):
    id: int
    active: bool

    class Config:
        from_attributes = True


class ContractRecordBase(BaseModel):
    template_id: int
    filled_fields: str


class ContractRecordCreate(ContractRecordBase):
    pass


class ContractRecordOut(ContractRecordBase):
    id: int
    status: str
    output_pdf_path: Optional[str] = None

    class Config:
        from_attributes = True
