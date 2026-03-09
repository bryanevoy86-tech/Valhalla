"""PACK 86: Narrative Documentary Engine - Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NarrativeEventBase(BaseModel):
    category: str
    title: str
    description: str
    emotion_level: str | None = None


class NarrativeEventCreate(NarrativeEventBase):
    pass


class NarrativeEventOut(NarrativeEventBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NarrativeChapterBase(BaseModel):
    title: str
    chapter_payload: str


class NarrativeChapterCreate(NarrativeChapterBase):
    pass


class NarrativeChapterOut(NarrativeChapterBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
