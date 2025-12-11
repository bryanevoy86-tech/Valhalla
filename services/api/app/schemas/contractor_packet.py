"""PACK 70: Contractor Packet Schemas
Pydantic models for contractor packet validation.
"""

from pydantic import BaseModel
from typing import Optional


class ContractorPacketBase(BaseModel):
    blueprint_id: int
    material_list: str
    task_breakdown: str
    notes: Optional[str] = None


class ContractorPacketCreate(ContractorPacketBase):
    pass


class ContractorPacketOut(ContractorPacketBase):
    id: int

    class Config:
        from_attributes = True
