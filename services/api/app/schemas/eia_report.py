"""
PACK CL18: EIA Report Schemas
"""

from pydantic import BaseModel


class EIAReportGenerateIn(BaseModel):
    period: str  # "YYYY-MM"
    title: str
    notes: str | None = None
