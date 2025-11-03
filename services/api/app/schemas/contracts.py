"""
Pydantic schemas for contract templates and generated records.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any


class TemplateIn(BaseModel):
    name: str = Field(..., max_length=160)
    version: Optional[str] = None
    notes: Optional[str] = None
    body_text: str


class TemplateOut(TemplateIn):
    id: int
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
