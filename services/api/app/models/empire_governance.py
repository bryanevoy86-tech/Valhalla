"""
PACK SO: Long-Term Empire Governance Map
Models for role definitions, hierarchies, and succession planning
"""
from sqlalchemy import String, Integer, Text, DateTime, Boolean, JSON, Column
from sqlalchemy.sql import func
from app.models.base import Base


class EmpireRole(Base):
    """Role definition with domain authority and permissions."""
    __tablename__ = 'empire_roles'
    
    id = Column(Integer, primary_key=True)
    role_id = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)  # King, Queen, Odin, Loki, Tyr, etc.
    domain = Column(JSON, nullable=True)  # {finance: bool, operations: bool, family: bool, risk: bool, automation: bool}
    permissions = Column(JSON, nullable=True)  # [{action: str, allowed: bool, notes: str}]
    responsibilities = Column(JSON, nullable=True)  # [string]: what this role owns
    authority_level = Column(Integer, nullable=True)  # 1-10, user-defined
    override_authority = Column(JSON, nullable=True)  # [string]: roles this one can override
    override_by = Column(JSON, nullable=True)  # [string]: roles that can override this one
    notes = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, server_default='active')  # active, inactive, suspended
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())


class RoleHierarchy(Base):
    """Relationship and override rules between roles."""
    __tablename__ = 'role_hierarchies'
    
    id = Column(Integer, primary_key=True)
    hierarchy_id = Column(String(255), nullable=False, unique=True)
    superior_role_id = Column(String(255), nullable=False)
    subordinate_role_id = Column(String(255), nullable=False)
    override_rules = Column(Text, nullable=True)  # Conditions when override is allowed
    escalation_path = Column(String(255), nullable=True)  # Next role in escalation
    context = Column(String(100), nullable=True)  # finance, operations, family, risk, etc.
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())


class SuccessionPlan(Base):
    """Abstract succession framework for role continuity."""
    __tablename__ = 'succession_plans'
    
    id = Column(Integer, primary_key=True)
    plan_id = Column(String(255), nullable=False, unique=True)
    triggered_role = Column(String(255), nullable=False)  # Role being replaced
    trigger_condition = Column(String(255), nullable=True)  # What causes succession
    description = Column(Text, nullable=True)
    fallback_roles = Column(JSON, nullable=True)  # [string]: ordered list of backup roles
    temporary_authority = Column(JSON, nullable=True)  # {role: authority_level} during transition
    documents_required = Column(JSON, nullable=True)  # [string]: what needs to be reviewed
    review_frequency = Column(String(50), nullable=True)  # yearly, quarterly, etc.
    last_reviewed = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())


class EmpireGovernanceMap(Base):
    """High-level governance summary and escalation paths."""
    __tablename__ = 'empire_governance_maps'
    
    id = Column(Integer, primary_key=True)
    map_id = Column(String(255), nullable=False, unique=True)
    version = Column(Integer, nullable=False, server_default=1)
    roles_count = Column(Integer, nullable=False)
    role_graph = Column(JSON, nullable=True)  # Complete role hierarchy as JSON
    conflict_rules = Column(JSON, nullable=True)  # [{roles, resolution_path, notes}]
    escalation_rules = Column(JSON, nullable=True)  # [{trigger, next_role, max_wait_time}]
    authority_matrix = Column(JSON, nullable=True)  # Matrix of role → permission → allowed
    risk_thresholds = Column(JSON, nullable=True)  # {domain: threshold_value}
    automation_rules = Column(JSON, nullable=True)  # [{trigger, executor_role, conditions}]
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
