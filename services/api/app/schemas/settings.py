from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GlobalSettingBase(BaseModel):
    key: str
    value: str
    category: Optional[str] = "core"
    description: Optional[str] = None
    is_feature_flag: bool = False


class GlobalSettingCreate(GlobalSettingBase):
    pass


class GlobalSettingUpdate(BaseModel):
    value: Optional[str]
    category: Optional[str]
    description: Optional[str]
    is_feature_flag: Optional[bool]


class GlobalSettingOut(GlobalSettingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
