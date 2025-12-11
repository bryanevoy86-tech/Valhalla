"""
PACK AO: Explainability Schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class ExplanationRequest(BaseModel):
    context_type: str
    context_id: Optional[str] = None
    payload: Dict[str, Any]   # scores, metrics, etc.


class ExplanationOut(BaseModel):
    id: int
    context_type: str
    context_id: Optional[str]
    explanation: str
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
