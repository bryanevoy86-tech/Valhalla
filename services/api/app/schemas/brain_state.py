"""
PACK AL: Brain State Snapshot Schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class BrainStateCreate(BaseModel):
    label: Optional[str] = None
    created_by: Optional[str] = None


class BrainStateOut(BaseModel):
    id: int
    label: Optional[str]
    empire_dashboard: Dict[str, Any]
    analytics_snapshot: Dict[str, Any]
    scenarios_summary: Dict[str, Any]
    created_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
