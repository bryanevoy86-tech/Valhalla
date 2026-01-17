"""
PACK SO: Long-Term Empire Governance Map
Service functions for role definitions and governance management
"""
from sqlalchemy.orm import Session
from app.models.empire_governance import EmpireRole, RoleHierarchy, SuccessionPlan, EmpireGovernanceMap
from datetime import datetime
from typing import List, Optional, Dict, Any


def create_empire_role(
    db: Session,
    role_id: str,
    name: str,
    domain: Optional[Dict[str, bool]] = None,
    permissions: Optional[List[Dict[str, Any]]] = None,
    responsibilities: Optional[List[str]] = None,
    authority_level: Optional[int] = None,
    override_authority: Optional[List[str]] = None,
    override_by: Optional[List[str]] = None,
    notes: Optional[str] = None
) -> EmpireRole:
    """Create an empire role."""
    role = EmpireRole(
        role_id=role_id,
        name=name,
        domain=domain,
        permissions=permissions,
        responsibilities=responsibilities,
        authority_level=authority_level,
        override_authority=override_authority,
        override_by=override_by,
        notes=notes,
        status="active"
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def list_active_roles(db: Session) -> List[EmpireRole]:
    """List all active empire roles."""
    return db.query(EmpireRole).filter(EmpireRole.status == "active").all()


def get_role_by_name(db: Session, name: str) -> Optional[EmpireRole]:
    """Get a role by name."""
    return db.query(EmpireRole).filter(EmpireRole.name == name).first()


def create_role_hierarchy(
    db: Session,
    hierarchy_id: str,
    superior_role_id: str,
    subordinate_role_id: str,
    override_rules: Optional[str] = None,
    escalation_path: Optional[str] = None,
    context: Optional[str] = None,
    notes: Optional[str] = None
) -> RoleHierarchy:
    """Define hierarchy relationship between roles."""
    hierarchy = RoleHierarchy(
        hierarchy_id=hierarchy_id,
        superior_role_id=superior_role_id,
        subordinate_role_id=subordinate_role_id,
        override_rules=override_rules,
        escalation_path=escalation_path,
        context=context,
        notes=notes
    )
    db.add(hierarchy)
    db.commit()
    db.refresh(hierarchy)
    return hierarchy


def list_role_hierarchy(db: Session) -> List[RoleHierarchy]:
    """List all role relationships."""
    return db.query(RoleHierarchy).all()


def create_succession_plan(
    db: Session,
    plan_id: str,
    triggered_role: str,
    trigger_condition: Optional[str] = None,
    description: Optional[str] = None,
    fallback_roles: Optional[List[str]] = None,
    temporary_authority: Optional[Dict[str, int]] = None,
    documents_required: Optional[List[str]] = None,
    review_frequency: Optional[str] = None,
    notes: Optional[str] = None
) -> SuccessionPlan:
    """Create a succession plan."""
    plan = SuccessionPlan(
        plan_id=plan_id,
        triggered_role=triggered_role,
        trigger_condition=trigger_condition,
        description=description,
        fallback_roles=fallback_roles,
        temporary_authority=temporary_authority,
        documents_required=documents_required,
        review_frequency=review_frequency,
        notes=notes
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def list_succession_plans(db: Session) -> List[SuccessionPlan]:
    """List all succession plans."""
    return db.query(SuccessionPlan).all()


def create_governance_map(
    db: Session,
    map_id: str,
    version: int,
    roles_count: int,
    role_graph: Optional[Dict[str, Any]] = None,
    conflict_rules: Optional[List[Dict[str, Any]]] = None,
    escalation_rules: Optional[List[Dict[str, Any]]] = None,
    authority_matrix: Optional[Dict[str, Dict[str, bool]]] = None,
    risk_thresholds: Optional[Dict[str, int]] = None,
    automation_rules: Optional[List[Dict[str, Any]]] = None,
    notes: Optional[str] = None
) -> EmpireGovernanceMap:
    """Create a governance map snapshot."""
    governance_map = EmpireGovernanceMap(
        map_id=map_id,
        version=version,
        roles_count=roles_count,
        role_graph=role_graph,
        conflict_rules=conflict_rules,
        escalation_rules=escalation_rules,
        authority_matrix=authority_matrix,
        risk_thresholds=risk_thresholds,
        automation_rules=automation_rules,
        notes=notes
    )
    db.add(governance_map)
    db.commit()
    db.refresh(governance_map)
    return governance_map


def get_latest_governance_map(db: Session) -> Optional[EmpireGovernanceMap]:
    """Get the latest governance map."""
    return db.query(EmpireGovernanceMap).order_by(EmpireGovernanceMap.version.desc()).first()


def calculate_governance_status(db: Session) -> Dict[str, Any]:
    """Calculate current governance structure status."""
    roles = db.query(EmpireRole).filter(EmpireRole.status == "active").count()
    hierarchies = db.query(RoleHierarchy).count()
    plans = db.query(SuccessionPlan).count()
    
    latest_map = get_latest_governance_map(db)
    
    return {
        "total_roles": roles,
        "role_relationships": hierarchies,
        "succession_plans": plans,
        "governance_version": latest_map.version if latest_map else 0,
        "last_updated": latest_map.updated_at if latest_map else None
    }
