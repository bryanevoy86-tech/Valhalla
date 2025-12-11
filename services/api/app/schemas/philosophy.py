"""
PACK TM: Core Philosophy Archive Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class PhilosophyRecordCreate(BaseModel):
    title: str
    pillars: Optional[str] = None
    mission_statement: Optional[str] = None
    values: Optional[str] = None
    rules_to_follow: Optional[str] = None
    rules_to_never_break: Optional[str] = None
    long_term_intent: Optional[str] = None
    notes: Optional[str] = None


class PhilosophyRecordOut(PhilosophyRecordCreate):
    id: int
    date: datetime

    class Config:
        from_attributes = True


class EmpirePrincipleCreate(BaseModel):
    category: str
    description: str
    enforcement_level: str = "soft"
    notes: Optional[str] = None


class EmpirePrincipleOut(EmpirePrincipleCreate):
    id: int

    class Config:
        from_attributes = True


class PhilosophySnapshot(BaseModel):
    latest_record: PhilosophyRecordOut
    principles: List[EmpirePrincipleOut]
