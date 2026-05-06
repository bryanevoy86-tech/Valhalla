"""Role-based access control for VA Intake system."""
from enum import Enum
from fastapi import HTTPException, status


class Role(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
    BRYAN = "bryan"
    VA = "va"
    VIEWER = "viewer"


class Permissions:
    """Define what each role can do."""
    
    ROLE_PERMISSIONS = {
        Role.ADMIN: {
            "submit_lead": True,
            "view_leads": True,
            "view_own_leads": True,
            "approve_lead": True,
            "deny_lead": True,
            "convert_to_deal": True,
            "view_audit": True,
            "view_sensitive": True,
            "export_data": True,
            "seed_test_data": True,
        },
        Role.BRYAN: {
            "submit_lead": False,
            "view_leads": True,
            "view_own_leads": False,
            "approve_lead": True,
            "deny_lead": True,
            "convert_to_deal": True,
            "view_audit": True,
            "view_sensitive": True,
            "export_data": True,
            "seed_test_data": False,
        },
        Role.VA: {
            "submit_lead": True,
            "view_leads": True,
            "view_own_leads": True,
            "approve_lead": False,
            "deny_lead": False,
            "convert_to_deal": False,
            "view_audit": False,
            "view_sensitive": False,
            "export_data": False,
            "seed_test_data": False,
        },
        Role.VIEWER: {
            "submit_lead": False,
            "view_leads": True,
            "view_own_leads": False,
            "approve_lead": False,
            "deny_lead": False,
            "convert_to_deal": False,
            "view_audit": False,
            "view_sensitive": False,
            "export_data": False,
            "seed_test_data": False,
        },
    }

    @staticmethod
    def check_permission(role: Role, permission: str) -> bool:
        """Check if a role has a specific permission."""
        if role not in Permissions.ROLE_PERMISSIONS:
            return False
        
        return Permissions.ROLE_PERMISSIONS[role].get(permission, False)

    @staticmethod
    def require_permission(role: Role, permission: str) -> None:
        """Raise exception if role lacks permission."""
        if not Permissions.check_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' lacks permission: '{permission}'"
            )


def get_user_role() -> Role:
    """
    Get current user's role from request context.
    
    For development, returns ADMIN.
    In production, will extract from JWT token.
    
    Returns:
        Role: Current user's role
    """
    # TODO: Extract from JWT token in production
    # For now, default to admin for development
    return Role.ADMIN


def require_role(*allowed_roles: Role):
    """Dependency for requiring specific roles."""
    def check_role():
        current_role = get_user_role()
        if current_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(str(r) for r in allowed_roles)}"
            )
        return current_role
    
    return check_role
