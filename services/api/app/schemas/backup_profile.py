from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BackupProfileBase(BaseModel):
    name: str
    target_type: str
    target_identifier: str
    frequency: str = "daily"
    retention_days: int = 30
    encrypted: bool = True
    encryption_profile: Optional[str] = None
    offsite_copy: bool = True
    notes: Optional[str] = None


class BackupProfileCreate(BackupProfileBase):
    pass


class BackupProfileUpdate(BaseModel):
    frequency: Optional[str]
    retention_days: Optional[int]
    encrypted: Optional[bool]
    encryption_profile: Optional[str]
    offsite_copy: Optional[bool]
    notes: Optional[str]


class BackupProfileOut(BackupProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
