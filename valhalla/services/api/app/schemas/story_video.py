"""PACK 67: Story Video Schemas
Pydantic models for story video validation.
"""

from pydantic import BaseModel
from typing import Optional


class StoryVideoBase(BaseModel):
    source_module: str
    script_payload: str


class StoryVideoCreate(StoryVideoBase):
    pass


class StoryVideoOut(StoryVideoBase):
    id: int
    status: str
    output_path: Optional[str] = None

    class Config:
        from_attributes = True
