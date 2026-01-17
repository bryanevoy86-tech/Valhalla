"""
Pydantic schemas for Influence Library.
"""
from pydantic import BaseModel
from datetime import datetime

class TechniqueCreate(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None

class TechniqueOut(BaseModel):
    id: int
    name: str
    description: str | None
    category: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class BiasCreate(BaseModel):
    name: str
    description: str | None = None
    mitigation: str | None = None

class BiasOut(BaseModel):
    id: int
    name: str
    description: str | None
    mitigation: str | None
    created_at: datetime

    class Config:
        from_attributes = True
