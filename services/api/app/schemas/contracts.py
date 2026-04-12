from __future__ import annotations

from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Any, Dict, List, Optional
from datetime import datetime
from app.models.contracts import ContractState, ContractPartyRole, ContractDocKind, SignProvider


# Template management schemas
class TemplateIn(BaseModel):
    name: str
    version: str = "1.0"
    notes: Optional[str] = None
    body_text: str


class TemplateOut(BaseModel):
    id: int
    name: str
    version: str
    notes: Optional[str]
    body_text: str
    
    model_config = ConfigDict(from_attributes=True)


# Contract generation schemas
class GenerateIn(BaseModel):
    template_id: int
    filename: str
    data: Dict[str, Any] = Field(default_factory=dict)


class RecordOut(BaseModel):
    id: int
    template_id: int
    filename: str
    pdf_path: Optional[str] = None
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class PartyIn(BaseModel):
    role: ContractPartyRole
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    must_sign: bool = True


class ContractCreateIn(BaseModel):
    template_code: str
    title: str
    deal_id: Optional[str] = None
    zone_id: Optional[str] = None
    merge_data: Dict[str, Any] = Field(default_factory=dict)
    parties: List[PartyIn] = Field(default_factory=list)
    sign_provider: SignProvider = SignProvider.SANDBOX


class ContractStateChangeIn(BaseModel):
    target: ContractState
    note: Optional[str] = None


class UploadDocIn(BaseModel):
    filename: str
    content_type: str = "application/pdf"
    kind: ContractDocKind = ContractDocKind.DRAFT


class SendForSignatureIn(BaseModel):
    subject: str = "Please sign"
    message: str = "Please review and sign the attached document."


class ContractOut(BaseModel):
    id: str
    template_id: str
    title: str
    state: ContractState
    deal_id: Optional[str]
    zone_id: Optional[str]
    sign_provider: SignProvider
    active_envelope_id: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventOut(BaseModel):
    id: str
    event_type: str
    actor: Optional[str]
    meta: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class GenerateIn(BaseModel):
    template_id: int
    filename: str = Field(..., max_length=200)  # e.g., "assignment_{{deal_id}}.pdf"
    data: Dict[str, Any] = {}


class RecordOut(BaseModel):
    id: int
    filename: str
    template_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)
