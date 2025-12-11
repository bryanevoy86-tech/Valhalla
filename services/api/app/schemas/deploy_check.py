# services/api/app/schemas/deploy_check.py

"""
Pydantic schemas for PACK V: Deployment Checklist
Typed responses for deployment readiness checks.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class EnvCheckResult(BaseModel):
    """Environment variable check results."""
    ok: bool = Field(..., description="Are all required env vars present?")
    details: Dict[str, bool] = Field(..., description="Per-variable presence status")


class DBCheckResult(BaseModel):
    """Database health check results."""
    ok: bool = Field(..., description="Is database connection healthy?")
    message: Optional[str] = Field(None, description="Health check message")


class RoutesCheckResult(BaseModel):
    """Route availability check results."""
    total_routes: int = Field(..., description="Total registered routes")
    required_prefixes: List[str] = Field(..., description="Required route prefixes")
    missing_prefixes: List[str] = Field(..., description="Missing route prefixes")
    ok: bool = Field(..., description="Are all required routes registered?")


class DeploymentChecks(BaseModel):
    """All deployment readiness checks."""
    environment: EnvCheckResult
    database: DBCheckResult
    routes: RoutesCheckResult


class DeploymentCheckResult(BaseModel):
    """Complete deployment readiness check result."""
    timestamp: str = Field(..., description="Check timestamp (ISO 8601)")
    overall_ok: bool = Field(..., description="Is the system ready to deploy?")
    checks: DeploymentChecks = Field(..., description="Detailed check results")
