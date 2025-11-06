"""
RBAC middleware and dependencies for FastAPI route protection.
"""
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from .service import RBACService


class RBACMiddleware:
    """Middleware for role-based access control."""
    
    @staticmethod
    def require_role(required_role: str):
        """
        Dependency that requires a specific role.
        Usage: @router.get("/admin", dependencies=[Depends(RBACMiddleware.require_role("admin"))])
        """
        def check_role(user_id: int, db: Session = Depends(get_db)):
            service = RBACService(db)
            if not service.user_has_role(user_id, required_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required role: {required_role}"
                )
            return True
        return check_role
    
    @staticmethod
    def require_any_role(required_roles: List[str]):
        """
        Dependency that requires any one of the specified roles.
        Usage: @router.get("/protected", dependencies=[Depends(RBACMiddleware.require_any_role(["admin", "manager"]))])
        """
        def check_roles(user_id: int, db: Session = Depends(get_db)):
            service = RBACService(db)
            user_roles = service.get_user_roles(user_id)
            user_role_names = {r.role_name for r in user_roles}
            
            if not any(role in user_role_names for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required one of: {', '.join(required_roles)}"
                )
            return True
        return check_roles
    
    @staticmethod
    def require_permission(required_permission: str):
        """
        Dependency that requires a specific permission.
        Usage: @router.delete("/users/{id}", dependencies=[Depends(RBACMiddleware.require_permission("delete:users"))])
        """
        def check_permission(user_id: int, db: Session = Depends(get_db)):
            service = RBACService(db)
            if not service.user_has_permission(user_id, required_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required permission: {required_permission}"
                )
            return True
        return check_permission
    
    @staticmethod
    def require_any_permission(required_permissions: List[str]):
        """
        Dependency that requires any one of the specified permissions.
        """
        def check_permissions(user_id: int, db: Session = Depends(get_db)):
            service = RBACService(db)
            user_permissions = service.get_user_permissions(user_id)
            
            if not any(perm in user_permissions for perm in required_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required one of: {', '.join(required_permissions)}"
                )
            return True
        return check_permissions


# Convenience function for checking roles and permissions
def check_user_role(user_id: int, role_name: str, db: Session) -> bool:
    """Check if a user has a specific role."""
    service = RBACService(db)
    return service.user_has_role(user_id, role_name)


def check_user_permission(user_id: int, permission_name: str, db: Session) -> bool:
    """Check if a user has a specific permission."""
    service = RBACService(db)
    return service.user_has_permission(user_id, permission_name)


def get_user_roles_list(user_id: int, db: Session) -> List[str]:
    """Get list of role names for a user."""
    service = RBACService(db)
    roles = service.get_user_roles(user_id)
    return [r.role_name for r in roles]


def get_user_permissions_set(user_id: int, db: Session) -> set:
    """Get set of permission names for a user."""
    service = RBACService(db)
    return service.get_user_permissions(user_id)
