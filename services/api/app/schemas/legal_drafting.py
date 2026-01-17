"""PACK 91: Legal Drafting - Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class LegalTemplateBase(BaseModel):
    title: str
    category: str
    body: str


class LegalTemplateCreate(LegalTemplateBase):
    pass


class LegalTemplateOut(LegalTemplateBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LegalDraftBase(BaseModel):
    template_id: int
    filled_payload: str
    output_path: str | None = None


class LegalDraftCreate(LegalDraftBase):
    pass


class LegalDraftOut(LegalDraftBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
