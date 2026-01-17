"""
PACK W: System Status Schemas
Typed Pydantic models for system status responses.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class PackInfo(BaseModel):
    """Information about a single pack in the system."""
    
    id: str = Field(..., description="Pack identifier (A-Z)")
    name: str = Field(..., description="Human-readable pack name")
    status: str = Field(
        default="installed",
        description="Pack status: 'installed', 'pending', 'deprecated', 'experimental'"
    )
    
    class Config:
        from_attributes = True


class SystemStatus(BaseModel):
    """Overall system status and configuration."""
    
    version: str = Field(
        ...,
        description="Semantic version (major.minor.patch)"
    )
    
    backend_complete: bool = Field(
        ...,
        description="Whether backend is marked as complete/production-ready"
    )
    
    packs: List[PackInfo] = Field(
        ...,
        description="List of installed packs with status"
    )
    
    summary: str = Field(
        ...,
        description="Human-readable summary of what this backend does"
    )
    
    extra: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata (notes, timestamps, etc.)"
    )
    
    class Config:
        from_attributes = True


class SystemStatusUpdate(BaseModel):
    """Request model for updating system status."""
    
    notes: Optional[str] = Field(
        default=None,
        description="Notes or comments about the status change"
    )
    
    version: Optional[str] = Field(
        default=None,
        description="Optional version update"
    )
