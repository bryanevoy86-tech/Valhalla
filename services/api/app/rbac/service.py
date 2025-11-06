"""
Service layer for Role-Based Access Control (RBAC).
Handles business logic for roles, permissions, and assignments.
"""
from typing import List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import Role, Permission, RolePermission, UserRole
from .schemas import RoleCreate, PermissionCreate


class RBACService:
    """Service for managing roles, permissions, and access control."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============ Role Management ============
    
    def create_role(self, role_data: RoleCreate) -> Role:
        """Create a new role."""
        existing = self.db.query(Role).filter(Role.role_name == role_data.role_name).first()
        if existing:
            raise ValueError(f"Role '{role_data.role_name}' already exists")
        
        role = Role(**role_data.model_dump())
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def get_role(self, role_id: int) -> Optional[Role]:
        """Get role by ID."""
        return self.db.query(Role).filter(Role.role_id == role_id).first()
    
    def get_role_by_name(self, role_name: str) -> Optional[Role]:
        """Get role by name."""
        return self.db.query(Role).filter(Role.role_name == role_name).first()
    
    def list_roles(self) -> List[Role]:
        """List all roles."""
        return self.db.query(Role).all()
    
    def delete_role(self, role_id: int) -> bool:
        """Delete a role (cascade deletes role_permissions and user_roles)."""
        role = self.get_role(role_id)
        if not role:
            return False
        self.db.delete(role)
        self.db.commit()
        return True
    
    # ============ Permission Management ============
    
    def create_permission(self, perm_data: PermissionCreate) -> Permission:
        """Create a new permission."""
        existing = self.db.query(Permission).filter(
            Permission.permission_name == perm_data.permission_name
        ).first()
        if existing:
            raise ValueError(f"Permission '{perm_data.permission_name}' already exists")
        
        permission = Permission(**perm_data.model_dump())
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        return permission
    
    def get_permission(self, permission_id: int) -> Optional[Permission]:
        """Get permission by ID."""
        return self.db.query(Permission).filter(Permission.permission_id == permission_id).first()
    
    def get_permission_by_name(self, permission_name: str) -> Optional[Permission]:
        """Get permission by name."""
        return self.db.query(Permission).filter(
            Permission.permission_name == permission_name
        ).first()
    
    def list_permissions(self) -> List[Permission]:
        """List all permissions."""
        return self.db.query(Permission).all()
    
    def delete_permission(self, permission_id: int) -> bool:
        """Delete a permission."""
        permission = self.get_permission(permission_id)
        if not permission:
            return False
        self.db.delete(permission)
        self.db.commit()
        return True
    
    # ============ Role-Permission Assignment ============
    
    def assign_permission_to_role(self, role_name: str, permission_name: str) -> RolePermission:
        """Assign a permission to a role."""
        role = self.get_role_by_name(role_name)
        if not role:
            raise ValueError(f"Role '{role_name}' not found")
        
        permission = self.get_permission_by_name(permission_name)
        if not permission:
            raise ValueError(f"Permission '{permission_name}' not found")
        
        # Check if already assigned
        existing = self.db.query(RolePermission).filter(
            and_(
                RolePermission.role_id == role.role_id,
                RolePermission.permission_id == permission.permission_id
            )
        ).first()
        
        if existing:
            raise ValueError(f"Permission '{permission_name}' already assigned to role '{role_name}'")
        
        role_perm = RolePermission(role_id=role.role_id, permission_id=permission.permission_id)
        self.db.add(role_perm)
        self.db.commit()
        return role_perm
    
    def remove_permission_from_role(self, role_name: str, permission_name: str) -> bool:
        """Remove a permission from a role."""
        role = self.get_role_by_name(role_name)
        permission = self.get_permission_by_name(permission_name)
        
        if not role or not permission:
            return False
        
        role_perm = self.db.query(RolePermission).filter(
            and_(
                RolePermission.role_id == role.role_id,
                RolePermission.permission_id == permission.permission_id
            )
        ).first()
        
        if not role_perm:
            return False
        
        self.db.delete(role_perm)
        self.db.commit()
        return True
    
    def get_role_permissions(self, role_name: str) -> List[Permission]:
        """Get all permissions for a role."""
        role = self.get_role_by_name(role_name)
        if not role:
            return []
        
        return self.db.query(Permission)\
            .join(RolePermission)\
            .filter(RolePermission.role_id == role.role_id)\
            .all()
    
    # ============ User-Role Assignment ============
    
    def assign_role_to_user(self, user_id: int, role_name: str, assigned_by: Optional[int] = None) -> UserRole:
        """Assign a role to a user."""
        role = self.get_role_by_name(role_name)
        if not role:
            raise ValueError(f"Role '{role_name}' not found")
        
        # Check if already assigned
        existing = self.db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == role.role_id
            )
        ).first()
        
        if existing:
            raise ValueError(f"Role '{role_name}' already assigned to user {user_id}")
        
        user_role = UserRole(user_id=user_id, role_id=role.role_id, assigned_by=assigned_by)
        self.db.add(user_role)
        self.db.commit()
        return user_role
    
    def remove_role_from_user(self, user_id: int, role_name: str) -> bool:
        """Remove a role from a user."""
        role = self.get_role_by_name(role_name)
        if not role:
            return False
        
        user_role = self.db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == role.role_id
            )
        ).first()
        
        if not user_role:
            return False
        
        self.db.delete(user_role)
        self.db.commit()
        return True
    
    def get_user_roles(self, user_id: int) -> List[Role]:
        """Get all roles assigned to a user."""
        return self.db.query(Role)\
            .join(UserRole)\
            .filter(UserRole.user_id == user_id)\
            .all()
    
    # ============ Permission Checking ============
    
    def user_has_permission(self, user_id: int, permission_name: str) -> bool:
        """Check if a user has a specific permission (through any of their roles)."""
        user_roles = self.get_user_roles(user_id)
        
        for role in user_roles:
            role_perms = self.get_role_permissions(role.role_name)
            if any(p.permission_name == permission_name for p in role_perms):
                return True
        
        return False
    
    def user_has_role(self, user_id: int, role_name: str) -> bool:
        """Check if a user has a specific role."""
        user_roles = self.get_user_roles(user_id)
        return any(r.role_name == role_name for r in user_roles)
    
    def get_user_permissions(self, user_id: int) -> Set[str]:
        """Get all unique permissions a user has through all their roles."""
        user_roles = self.get_user_roles(user_id)
        permissions = set()
        
        for role in user_roles:
            role_perms = self.get_role_permissions(role.role_name)
            permissions.update(p.permission_name for p in role_perms)
        
        return permissions
    
    def get_users_with_role(self, role_name: str) -> List[int]:
        """Get all user IDs that have a specific role."""
        role = self.get_role_by_name(role_name)
        if not role:
            return []
        
        user_roles = self.db.query(UserRole).filter(UserRole.role_id == role.role_id).all()
        return [ur.user_id for ur in user_roles]
    
    # ============ Bulk Operations ============
    
    def initialize_default_roles_and_permissions(self):
        """Initialize default roles and permissions for a new system."""
        # Create default roles
        default_roles = [
            {"role_name": "admin", "description": "Full system access"},
            {"role_name": "manager", "description": "Manage users and content"},
            {"role_name": "user", "description": "Standard user access"},
            {"role_name": "viewer", "description": "Read-only access"}
        ]
        
        for role_data in default_roles:
            try:
                self.create_role(RoleCreate(**role_data))
            except ValueError:
                pass  # Role already exists
        
        # Create default permissions
        default_permissions = [
            {"permission_name": "read:users", "resource": "users", "action": "read"},
            {"permission_name": "write:users", "resource": "users", "action": "write"},
            {"permission_name": "delete:users", "resource": "users", "action": "delete"},
            {"permission_name": "read:content", "resource": "content", "action": "read"},
            {"permission_name": "write:content", "resource": "content", "action": "write"},
            {"permission_name": "delete:content", "resource": "content", "action": "delete"},
            {"permission_name": "manage:roles", "resource": "roles", "action": "manage"},
            {"permission_name": "manage:permissions", "resource": "permissions", "action": "manage"},
        ]
        
        for perm_data in default_permissions:
            try:
                self.create_permission(PermissionCreate(**perm_data))
            except ValueError:
                pass  # Permission already exists
        
        # Assign permissions to roles
        role_permission_map = {
            "admin": ["read:users", "write:users", "delete:users", "read:content", "write:content", 
                     "delete:content", "manage:roles", "manage:permissions"],
            "manager": ["read:users", "write:users", "read:content", "write:content", "delete:content"],
            "user": ["read:users", "read:content", "write:content"],
            "viewer": ["read:users", "read:content"]
        }
        
        for role_name, permissions in role_permission_map.items():
            for perm_name in permissions:
                try:
                    self.assign_permission_to_role(role_name, perm_name)
                except ValueError:
                    pass  # Already assigned
        
        self.db.commit()
