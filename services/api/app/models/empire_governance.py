"""
PACK SO: Long-Term Empire Governance Map
Models for role definitions, hierarchies, and succession planning
"""
from sqlalchemy import String, Integer, Text, DateTime, Boolean, JSON
from datetime import datetime
from app.core.db import Base


class EmpireRole(Base):
    """Role definition with domain authority and permissions."""
    __tablename__ = 'empire_roles'
    
    id = Integer(primary_key=True)
    role_id = String(255, nullable=False, unique=True)
    name = String(255, nullable=False)  # King, Queen, Odin, Loki, Tyr, etc.
    domain = JSON(nullable=True)  # {finance: bool, operations: bool, family: bool, risk: bool, automation: bool}
    permissions = JSON(nullable=True)  # [{action: str, allowed: bool, notes: str}]
    responsibilities = JSON(nullable=True)  # [string]: what this role owns
    authority_level = Integer(nullable=True)  # 1-10, user-defined
    override_authority = JSON(nullable=True)  # [string]: roles this one can override
    override_by = JSON(nullable=True)  # [string]: roles that can override this one
    notes = Text(nullable=True)
    status = String(50, nullable=False, server_default='active')  # active, inactive, suspended
    created_at = DateTime(nullable=False, server_default=datetime.utcnow)
    updated_at = DateTime(nullable=False, server_default=datetime.utcnow, onupdate=datetime.utcnow)


class RoleHierarchy(Base):
    """Relationship and override rules between roles."""
    __tablename__ = 'role_hierarchies'
    
    id = Integer(primary_key=True)
    hierarchy_id = String(255, nullable=False, unique=True)
    superior_role_id = String(255, nullable=False)
    subordinate_role_id = String(255, nullable=False)
    override_rules = Text(nullable=True)  # Conditions when override is allowed
    escalation_path = String(255, nullable=True)  # Next role in escalation
    context = String(100, nullable=True)  # finance, operations, family, risk, etc.
    notes = Text(nullable=True)
    created_at = DateTime(nullable=False, server_default=datetime.utcnow)
    updated_at = DateTime(nullable=False, server_default=datetime.utcnow, onupdate=datetime.utcnow)


class SuccessionPlan(Base):
    """Abstract succession framework for role continuity."""
    __tablename__ = 'succession_plans'
    
    id = Integer(primary_key=True)
    plan_id = String(255, nullable=False, unique=True)
    triggered_role = String(255, nullable=False)  # Role being replaced
    trigger_condition = String(255, nullable=True)  # What causes succession
    description = Text(nullable=True)
    fallback_roles = JSON(nullable=True)  # [string]: ordered list of backup roles
    temporary_authority = JSON(nullable=True)  # {role: authority_level} during transition
    documents_required = JSON(nullable=True)  # [string]: what needs to be reviewed
    review_frequency = String(50, nullable=True)  # yearly, quarterly, etc.
    last_reviewed = DateTime(nullable=True)
    notes = Text(nullable=True)
    created_at = DateTime(nullable=False, server_default=datetime.utcnow)
    updated_at = DateTime(nullable=False, server_default=datetime.utcnow, onupdate=datetime.utcnow)


class EmpireGovernanceMap(Base):
    """High-level governance summary and escalation paths."""
    __tablename__ = 'empire_governance_maps'
    
    id = Integer(primary_key=True)
    map_id = String(255, nullable=False, unique=True)
    version = Integer(nullable=False, server_default=1)
    roles_count = Integer(nullable=False)
    role_graph = JSON(nullable=True)  # Complete role hierarchy as JSON
    conflict_rules = JSON(nullable=True)  # [{roles, resolution_path, notes}]
    escalation_rules = JSON(nullable=True)  # [{trigger, next_role, max_wait_time}]
    authority_matrix = JSON(nullable=True)  # Matrix of role → permission → allowed
    risk_thresholds = JSON(nullable=True)  # {domain: threshold_value}
    automation_rules = JSON(nullable=True)  # [{trigger, executor_role, conditions}]
    notes = Text(nullable=True)
    created_at = DateTime(nullable=False, server_default=datetime.utcnow)
    updated_at = DateTime(nullable=False, server_default=datetime.utcnow, onupdate=datetime.utcnow)
