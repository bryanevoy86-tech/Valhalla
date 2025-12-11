"""
PACK SO: Long-Term Empire Governance Map
Pydantic schemas for role definitions and succession planning
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class RolePermissionSchema(BaseModel):
    action: str = Field(..., description="Action that can be performed")
    allowed: bool = Field(default=True, description="Is this action allowed?")
    notes: Optional[str] = Field(None, description="Notes about this permission")


class EmpireRoleSchema(BaseModel):
    role_id: str = Field(..., description="Unique role identifier")
    name: str = Field(..., description="Role name (King, Queen, Odin, etc.)")
    domain: Optional[Dict[str, bool]] = Field(None, description="Domain authorities")
    permissions: Optional[List[RolePermissionSchema]] = Field(None, description="Role permissions")
    responsibilities: Optional[List[str]] = Field(None, description="What this role owns")
    authority_level: Optional[int] = Field(None, description="1-10 authority level")
    override_authority: Optional[List[str]] = Field(None, description="Roles this can override")
    override_by: Optional[List[str]] = Field(None, description="Roles that can override this")
    status: Optional[str] = Field("active", description="active, inactive, or suspended")
    notes: Optional[str] = Field(None, description="Role notes")
    
    class Config:
        from_attributes = True


class RoleHierarchySchema(BaseModel):
    hierarchy_id: str = Field(..., description="Unique hierarchy identifier")
    superior_role_id: str = Field(..., description="Superior role")
    subordinate_role_id: str = Field(..., description="Subordinate role")
    override_rules: Optional[str] = Field(None, description="Override conditions")
    escalation_path: Optional[str] = Field(None, description="Next role in escalation")
    context: Optional[str] = Field(None, description="Domain context")
    notes: Optional[str] = Field(None, description="Notes about relationship")
    
    class Config:
        from_attributes = True


class SuccessionPlanSchema(BaseModel):
    plan_id: str = Field(..., description="Unique plan identifier")
    triggered_role: str = Field(..., description="Role being replaced")
    trigger_condition: Optional[str] = Field(None, description="What causes succession")
    description: Optional[str] = Field(None, description="Plan description")
    fallback_roles: Optional[List[str]] = Field(None, description="Backup roles in order")
    temporary_authority: Optional[Dict[str, int]] = Field(None, description="Authority during transition")
    documents_required: Optional[List[str]] = Field(None, description="Required documents")
    review_frequency: Optional[str] = Field(None, description="Yearly, quarterly, etc.")
    notes: Optional[str] = Field(None, description="Plan notes")
    
    class Config:
        from_attributes = True


class EmpireGovernanceMapSchema(BaseModel):
    map_id: str = Field(..., description="Unique map identifier")
    version: int = Field(default=1, description="Map version number")
    roles_count: int = Field(..., description="Total number of roles")
    role_graph: Optional[Dict[str, Any]] = Field(None, description="Role hierarchy graph")
    conflict_rules: Optional[List[Dict[str, Any]]] = Field(None, description="Conflict resolution rules")
    escalation_rules: Optional[List[Dict[str, Any]]] = Field(None, description="Escalation paths")
    authority_matrix: Optional[Dict[str, Dict[str, bool]]] = Field(None, description="Role/permission matrix")
    risk_thresholds: Optional[Dict[str, int]] = Field(None, description="Risk thresholds by domain")
    automation_rules: Optional[List[Dict[str, Any]]] = Field(None, description="Automation rules")
    notes: Optional[str] = Field(None, description="Map notes")
    
    class Config:
        from_attributes = True


class GovernanceResponse(BaseModel):
    total_roles: int = Field(..., description="Total active roles")
    governance_version: int = Field(..., description="Current governance map version")
    active_hierarchy: Optional[Dict[str, Any]] = Field(None, description="Current role hierarchy")
    succession_plans_count: int = Field(..., description="Number of succession plans")
    last_updated: Optional[datetime] = Field(None, description="Last governance update")
