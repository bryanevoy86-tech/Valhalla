"""
FastAPI router for Role-Based Access Control (RBAC).
Provides endpoints for managing roles, permissions, and assignments.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.rbac.service import RBACService
from app.rbac.schemas import (
    RoleCreate, RoleOut, RoleWithPermissions,
    PermissionCreate, PermissionOut,
    UserRoleAssign, UserRoleOut, UserWithRoles,
    RolePermissionAssign, PermissionCheck
)


router = APIRouter(prefix="/rbac", tags=["rbac"])


# ============ Role Management Endpoints ============

@router.post("/roles", response_model=RoleOut, status_code=201)
async def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    """Create a new role."""
    service = RBACService(db)
    try:
        return service.create_role(role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/roles", response_model=List[RoleOut])
async def list_roles(db: Session = Depends(get_db)):
    """List all roles."""
    service = RBACService(db)
    return service.list_roles()


@router.get("/roles/{role_id}", response_model=RoleOut)
async def get_role(role_id: int, db: Session = Depends(get_db)):
    """Get a specific role by ID."""
    service = RBACService(db)
    role = service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.get("/roles/name/{role_name}", response_model=RoleOut)
async def get_role_by_name(role_name: str, db: Session = Depends(get_db)):
    """Get a specific role by name."""
    service = RBACService(db)
    role = service.get_role_by_name(role_name)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.delete("/roles/{role_id}")
async def delete_role(role_id: int, db: Session = Depends(get_db)):
    """Delete a role (cascade deletes assignments)."""
    service = RBACService(db)
    success = service.delete_role(role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    return {"ok": True, "message": "Role deleted successfully"}


# ============ Permission Management Endpoints ============

@router.post("/permissions", response_model=PermissionOut, status_code=201)
async def create_permission(permission: PermissionCreate, db: Session = Depends(get_db)):
    """Create a new permission."""
    service = RBACService(db)
    try:
        return service.create_permission(permission)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/permissions", response_model=List[PermissionOut])
async def list_permissions(db: Session = Depends(get_db)):
    """List all permissions."""
    service = RBACService(db)
    return service.list_permissions()


@router.get("/permissions/{permission_id}", response_model=PermissionOut)
async def get_permission(permission_id: int, db: Session = Depends(get_db)):
    """Get a specific permission by ID."""
    service = RBACService(db)
    permission = service.get_permission(permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return permission


@router.delete("/permissions/{permission_id}")
async def delete_permission(permission_id: int, db: Session = Depends(get_db)):
    """Delete a permission."""
    service = RBACService(db)
    success = service.delete_permission(permission_id)
    if not success:
        raise HTTPException(status_code=404, detail="Permission not found")
    return {"ok": True, "message": "Permission deleted successfully"}


# ============ Role-Permission Assignment Endpoints ============

@router.post("/role-permissions/assign")
async def assign_permission_to_role(
    assignment: RolePermissionAssign,
    db: Session = Depends(get_db)
):
    """Assign a permission to a role."""
    service = RBACService(db)
    try:
        service.assign_permission_to_role(assignment.role_name, assignment.permission_name)
        return {"ok": True, "message": f"Permission '{assignment.permission_name}' assigned to role '{assignment.role_name}'"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/role-permissions/remove")
async def remove_permission_from_role(
    assignment: RolePermissionAssign,
    db: Session = Depends(get_db)
):
    """Remove a permission from a role."""
    service = RBACService(db)
    success = service.remove_permission_from_role(assignment.role_name, assignment.permission_name)
    if not success:
        raise HTTPException(status_code=404, detail="Role or permission not found")
    return {"ok": True, "message": f"Permission '{assignment.permission_name}' removed from role '{assignment.role_name}'"}


@router.get("/role-permissions/{role_name}", response_model=RoleWithPermissions)
async def get_role_permissions(role_name: str, db: Session = Depends(get_db)):
    """Get all permissions for a role."""
    service = RBACService(db)
    role = service.get_role_by_name(role_name)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    permissions = service.get_role_permissions(role_name)
    return {"role": role, "permissions": permissions}


# ============ User-Role Assignment Endpoints ============

@router.post("/user-roles/assign")
async def assign_role_to_user(
    assignment: UserRoleAssign,
    db: Session = Depends(get_db)
):
    """Assign a role to a user."""
    service = RBACService(db)
    try:
        service.assign_role_to_user(
            assignment.user_id,
            assignment.role_name,
            assignment.assigned_by
        )
        return {"ok": True, "message": f"Role '{assignment.role_name}' assigned to user {assignment.user_id}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/user-roles/remove")
async def remove_role_from_user(
    user_id: int,
    role_name: str,
    db: Session = Depends(get_db)
):
    """Remove a role from a user."""
    service = RBACService(db)
    success = service.remove_role_from_user(user_id, role_name)
    if not success:
        raise HTTPException(status_code=404, detail="User role assignment not found")
    return {"ok": True, "message": f"Role '{role_name}' removed from user {user_id}"}


@router.get("/user-roles/{user_id}", response_model=UserWithRoles)
async def get_user_roles(user_id: int, db: Session = Depends(get_db)):
    """Get all roles assigned to a user."""
    service = RBACService(db)
    roles = service.get_user_roles(user_id)
    return {"user_id": user_id, "roles": roles}


# ============ Permission Checking Endpoints ============

@router.get("/check-permission/{user_id}/{permission_name}", response_model=PermissionCheck)
async def check_user_permission(
    user_id: int,
    permission_name: str,
    db: Session = Depends(get_db)
):
    """Check if a user has a specific permission."""
    service = RBACService(db)
    has_permission = service.user_has_permission(user_id, permission_name)
    
    # Get roles that grant this permission
    user_roles = service.get_user_roles(user_id)
    granted_by = []
    
    for role in user_roles:
        # Ensure proper typing for static analyzers; at runtime, role.role_name is a string
        role_name_str = str(getattr(role, "role_name", ""))
        role_perms = service.get_role_permissions(role_name_str)
        if any(p.permission_name == permission_name for p in role_perms):
            granted_by.append(role_name_str)
    
    return {
        "user_id": user_id,
        "permission_name": permission_name,
        "has_permission": has_permission,
        "granted_by_roles": granted_by
    }


@router.get("/check-role/{user_id}/{role_name}")
async def check_user_role(
    user_id: int,
    role_name: str,
    db: Session = Depends(get_db)
):
    """Check if a user has a specific role."""
    service = RBACService(db)
    has_role = service.user_has_role(user_id, role_name)
    return {"user_id": user_id, "role_name": role_name, "has_role": has_role}


@router.get("/user-permissions/{user_id}")
async def get_user_permissions(user_id: int, db: Session = Depends(get_db)):
    """Get all permissions a user has through all their roles."""
    service = RBACService(db)
    permissions = service.get_user_permissions(user_id)
    return {"user_id": user_id, "permissions": list(permissions)}


# ============ Utility Endpoints ============

@router.post("/initialize-defaults")
async def initialize_default_roles_and_permissions(db: Session = Depends(get_db)):
    """Initialize default roles (admin, manager, user, viewer) and permissions."""
    service = RBACService(db)
    service.initialize_default_roles_and_permissions()
    return {
        "ok": True,
        "message": "Default roles and permissions initialized",
        "roles": ["admin", "manager", "user", "viewer"],
        "note": "Default permissions assigned to roles"
    }


@router.get("/users-with-role/{role_name}")
async def get_users_with_role(role_name: str, db: Session = Depends(get_db)):
    """Get all user IDs that have a specific role."""
    service = RBACService(db)
    user_ids = service.get_users_with_role(role_name)
    return {"role_name": role_name, "user_ids": user_ids, "count": len(user_ids)}
