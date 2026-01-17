"""PACK 74: Data IO Schemas
Pydantic models for import/export jobs.
"""

from pydantic import BaseModel
from typing import Optional


class ImportJobBase(BaseModel):
    target_model: str
    file_path: str


class ImportJobCreate(ImportJobBase):
    pass


class ImportJobOut(ImportJobBase):
    id: int
    status: str
    error_report: Optional[str] = None

    class Config:
        from_attributes = True


class ExportJobBase(BaseModel):
    source_model: str
    filter_payload: Optional[str] = None


class ExportJobCreate(ExportJobBase):
    pass


class ExportJobOut(ExportJobBase):
    id: int
    status: str
    download_path: Optional[str] = None

    class Config:
        from_attributes = True
