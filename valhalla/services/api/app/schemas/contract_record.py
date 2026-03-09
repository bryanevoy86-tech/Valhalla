# services/api/app/schemas/contract_record.py

from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ContractCreate(BaseModel):
    deal_id: int
    title: str = Field(..., description="Contract title/description")
    professional_id: Optional[int] = Field(None, description="Professional reviewing/drafting")
    storage_url: Optional[str] = Field(None, description="Document storage URL (S3, Drive, etc.)")


class ContractUpdateStatus(BaseModel):
    status: str = Field(
        ...,
        description="Contract status: draft, under_review, approved, sent, signed, archived"
    )
    storage_url: Optional[str] = Field(None, description="Updated document URL")


class ContractOut(BaseModel):
    id: int
    deal_id: int
    professional_id: Optional[int]
    status: str
    version: int
    storage_url: Optional[str]
    title: str
    created_at: datetime
    updated_at: datetime
    signed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
