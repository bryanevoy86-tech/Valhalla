"""
PACK AC: Content / Media Engine Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MediaChannelCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None


class MediaChannelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class MediaChannelOut(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MediaContentCreate(BaseModel):
    title: str
    content_type: str
    body: str
    tags: Optional[str] = None
    audience: Optional[str] = None


class MediaContentOut(BaseModel):
    id: int
    title: str
    content_type: str
    body: str
    tags: Optional[str]
    audience: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MediaPublishCreate(BaseModel):
    content_id: int
    channel_id: int
    status: str = "planned"
    external_ref: Optional[str] = None


class MediaPublishUpdate(BaseModel):
    status: Optional[str] = None
    external_ref: Optional[str] = None


class MediaPublishOut(BaseModel):
    id: int
    content_id: int
    channel_id: int
    status: str
    external_ref: Optional[str]
    published_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
