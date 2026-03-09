from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MasterConfigBase(BaseModel):
    config_key: str
    value_type: str = "string"
    value_string: Optional[str] = None
    value_float: Optional[float] = None
    value_int: Optional[int] = None
    value_bool: Optional[bool] = None
    value_json: Optional[str] = None
    description: Optional[str] = None
    ai_mutable: bool = False


class MasterConfigCreate(MasterConfigBase):
    pass


class MasterConfigUpdate(BaseModel):
    value_string: Optional[str]
    value_float: Optional[float]
    value_int: Optional[int]
    value_bool: Optional[bool]
    value_json: Optional[str]
    description: Optional[str]
    ai_mutable: Optional[bool]


class MasterConfigOut(MasterConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
