"""
PACK TU: Error & ProblemDetails Schemas
Standardized error responses with correlation_id.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ProblemDetails(BaseModel):
    type: Optional[str] = Field(
        default=None,
        description="URI reference that identifies the problem type."
    )
    title: str = Field(..., description="Short, human-readable summary of the problem.")
    status: int = Field(..., description="HTTP status code.")
    detail: Optional[str] = Field(
        default=None,
        description="Human-readable explanation specific to this occurrence."
    )
    instance: Optional[str] = Field(
        default=None,
        description="URI reference that identifies the specific occurrence."
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Correlation ID for tracing this error across services."
    )
    extra: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata."
    )
