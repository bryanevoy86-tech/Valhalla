# services/api/app/schemas/system_debug.py

"""
Pydantic schemas for PACK S debug endpoints.
Typed responses for route listing and system snapshot.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RouteInfo(BaseModel):
    """Info about a single registered route."""
    path: Optional[str] = Field(None, description="The URL path")
    name: Optional[str] = Field(None, description="Route name/identifier")
    methods: List[str] = Field(default_factory=list, description="HTTP methods (GET, POST, etc.)")


class DebugRoutesResponse(BaseModel):
    """Response for /debug/routes endpoint."""
    routes: List[RouteInfo] = Field(..., description="List of all registered routes")
    count: int = Field(..., description="Total number of routes")


class SystemSnapshot(BaseModel):
    """Response for /debug/system endpoint."""
    routes_count: int = Field(..., description="Number of registered routes")
    db_healthy: bool = Field(..., description="Is database connection healthy?")
    subsystems: Dict[str, bool] = Field(..., description="Health status of key subsystems")
    timestamp: str = Field(..., description="Snapshot timestamp (ISO 8601)")


class DebugSystemResponse(BaseModel):
    """Combined debug system response."""
    routes_count: int
    db_healthy: bool
    subsystems: Dict[str, bool]
    timestamp: Optional[str] = None
