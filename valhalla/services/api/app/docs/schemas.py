from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class DocTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    content: str
    meta: Optional[dict] = None


class DocTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str]
    content: str
    meta: Optional[dict]
    created_at: datetime


class GenerateDocRequest(BaseModel):
    template_id: int
    filename: str
    fields: dict  # e.g., {"client_name": "Acme Corp", "effective_date": "2025-01-15"}
    meta: Optional[dict] = None


class GeneratedDocResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    template_id: int
    filename: str
    content: str
    meta: Optional[dict]
    created_at: datetime


class SendForESignRequest(BaseModel):
    generated_doc_id: int
    recipients: list[dict]  # e.g., [{"email": "cfo@acme.com", "name": "CFO"}]
