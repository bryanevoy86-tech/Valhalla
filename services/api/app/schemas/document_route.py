# services/api/app/schemas/document_route.py

from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DocumentRouteCreate(BaseModel):
    deal_id: int
    professional_id: int
    document_type: str = Field(..., description="Type: contract, supporting_doc, summary, etc.")
    storage_url: str = Field(..., description="Document storage URL")
    contract_id: Optional[int] = Field(None, description="Associated contract ID if applicable")


class DocumentRouteUpdateStatus(BaseModel):
    status: str = Field(..., description="Status: sent, opened, acknowledged")


class DocumentRouteOut(BaseModel):
    id: int
    deal_id: int
    contract_id: Optional[int]
    professional_id: int
    document_type: str
    storage_url: str
    sent_at: datetime
    opened_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    status: str

    class Config:
        from_attributes = True
