"""
PACK AN: Auto-Heal & Integrity Monitor Schemas
"""

from typing import Dict, Any, List
from pydantic import BaseModel


class IntegrityIssue(BaseModel):
    category: str
    entity_type: str
    entity_id: str | int | None
    message: str


class IntegrityReport(BaseModel):
    total_issues: int
    issues: List[IntegrityIssue]
