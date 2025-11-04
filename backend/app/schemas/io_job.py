from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class ImportJobBase(BaseModel):
    org_id: int
    kind: str
    src_filename: str
    options: Optional[Any] = None


class ImportJobCreate(ImportJobBase):
    pass


class ImportJobUpdate(BaseModel):
    status: Optional[str]
    total_rows: Optional[int]
    success_rows: Optional[int]
    error_rows: Optional[int]
    finished_at: Optional[datetime]
    error_message: Optional[str]


class ImportJob(ImportJobBase):
    id: int
    status: str
    total_rows: Optional[int]
    success_rows: Optional[int]
    error_rows: Optional[int]
    created_at: datetime
    finished_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        orm_mode = True


class ImportRowErrorBase(BaseModel):
    job_id: int
    row_number: int
    data: Optional[Any]
    error: str


class ImportRowErrorCreate(ImportRowErrorBase):
    pass


class ImportRowError(ImportRowErrorBase):
    id: int

    class Config:
        orm_mode = True


class ExportJobBase(BaseModel):
    org_id: int
    kind: str
    filters: Optional[Any] = None


class ExportJobCreate(ExportJobBase):
    pass


class ExportJobUpdate(BaseModel):
    status: Optional[str]
    out_filename: Optional[str]
    finished_at: Optional[datetime]
    error_message: Optional[str]


class ExportJob(ExportJobBase):
    id: int
    status: str
    out_filename: Optional[str]
    created_at: datetime
    finished_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        orm_mode = True
