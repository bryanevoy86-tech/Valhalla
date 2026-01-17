"""PACK 68: Blueprint Generator Schemas
Pydantic models for blueprint validation.
"""

from pydantic import BaseModel
from typing import Optional


class BlueprintBase(BaseModel):
    project_name: str
    property_address: Optional[str] = None
    specs_payload: str


class BlueprintCreate(BlueprintBase):
    pass


class BlueprintOut(BlueprintBase):
    id: int
    status: str

    class Config:
        from_attributes = True
