from pydantic import BaseModel, AnyHttpUrl
from typing import Optional, Dict, Any


class LegacyInstanceBase(BaseModel):
    code: str
    region: str
    api_base: AnyHttpUrl
    status: Optional[str] = "ready"
    meta: Optional[Dict[str, Any]] = None


class LegacyInstanceCreate(LegacyInstanceBase):
    pass


class LegacyInstanceResponse(LegacyInstanceBase):
    id: int

    class Config:
        from_attributes = True


class ClonePlanCreate(BaseModel):
    source_instance_id: int
    target_region: str
    modules: Dict[str, bool]
    safe_mode: bool = True


class ClonePlanResponse(ClonePlanCreate):
    id: int
    status: str
    result: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class MirrorLinkCreate(BaseModel):
    primary_instance_id: int
    secondary_instance_id: int
    mode: str = "hot"
    traffic_split: int = 50
    active: bool = True


class MirrorLinkResponse(MirrorLinkCreate):
    id: int

    class Config:
        from_attributes = True
