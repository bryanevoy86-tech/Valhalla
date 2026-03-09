from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

class HeimdallBuildScope(BaseModel):
    """
    Scope controls what Heimdall is allowed to touch for this build.
    This is purely an intent/metadata model that your builder service
    can consume.
    """
    target_dirs: List[str] = Field(
        default_factory=list,
        description="List of directories Heimdall is allowed to modify (relative paths).",
    )
    max_files: int = Field(
        default=10,
        description="Maximum number of files Heimdall may edit in this task.",
    )
    allow_migrations: bool = Field(
        default=False,
        description="If True, Heimdall is allowed to create Alembic migrations.",
    )
    allow_new_routes: bool = Field(
        default=True,
        description="If True, Heimdall may create new router files/endpoints.",
    )
    allow_schema_changes: bool = Field(
        default=False,
        description="If True, Heimdall may change Pydantic/DB models.",
    )

class HeimdallBuildRequest(BaseModel):
    """
    High-level request describing what Heimdall should build.
    This is what YOU or other services call.
    Governance will decide if this should proceed.
    """
    title: str = Field(
        ...,
        description="Short human-readable name for the build task.",
    )
    description: str = Field(
        ...,
        description="Detailed description of what Heimdall should build or refactor.",
    )
    vertical: str = Field(
        ...,
        description="Business vertical this build supports (e.g. 'real_estate', 'makeup', 'education').",
    )
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="1-10 priority score for this build.",
    )
    # Estimates (used by Odin/Queen/Loki style checks)
    estimated_hours: int = Field(
        default=8,
        description="Estimated hours of work this build would represent for a human dev.",
    )
    complexity_score: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Self-rated 1-10 complexity for the build.",
    )
    estimated_annual_profit_impact: int = Field(
        default=0,
        description="Rough estimate of annual profit this feature could unlock (in local currency).",
    )
    strategic_importance: int = Field(
        default=5,
        ge=1,
        le=10,
        description="1-10: how important this is to Valhalla's mission.",
    )
    # Risk flags / metadata
    is_core_infrastructure: bool = Field(
        default=False,
        description="If True, Heimdall would touch core infra (DB, core services, auth, etc.).",
    )
    touches_financial_flows: bool = Field(
        default=False,
        description="If True, build touches money flows (profit allocation, FunFunds, taxes).",
    )
    touches_legal_contracts: bool = Field(
        default=False,
        description="If True, build touches legal docs or contract engine.",
    )
    experimental_only: bool = Field(
        default=False,
        description="If True, this is an experiment, not a production-critical change.",
    )
    # Governance overrides (advanced users)
    governance_flags: Dict[str, str] = Field(
        default_factory=dict,
        description="Optional raw flags to feed into governance (only for advanced use).",
    )
    scope: HeimdallBuildScope = Field(
        default_factory=HeimdallBuildScope,
        description="What Heimdall is allowed to touch for this task.",
    )

class HeimdallBuildResponse(BaseModel):
    """
    Result of a Heimdall build request.
    We return the governance decision and, if applicable, the builder task info.
    """
    accepted: bool = Field(
        ...,
        description="True if governance allowed the build request.",
    )
    governance: dict = Field(
        ...,
        description="Full governance aggregate decision payload.",
    )
    builder_task_created: bool = Field(
        default=False,
        description="True if a downstream /builder/tasks call succeeded.",
    )
    builder_task_id: Optional[str] = Field(
        default=None,
        description="Identifier of the created builder task, if any.",
    )
    builder_raw_response: Optional[dict] = Field(
        default=None,
        description="Raw JSON response from the builder service, if available.",
    )
    message: Optional[str] = None
