"""
PACK AK: Analytics / Metrics Engine Schemas
"""

from typing import Dict, Any
from pydantic import BaseModel


class AnalyticsSnapshot(BaseModel):
    holdings: Dict[str, Any]
    pipelines: Dict[str, Any]
    professionals: Dict[str, Any]
    children: Dict[str, Any]
    education: Dict[str, Any]
