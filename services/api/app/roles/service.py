from datetime import datetime

from .schemas import RoleOut


class RolesService:
    @staticmethod
    def get_role_permissions(role: str) -> RoleOut:
        r = (role or "").lower()
        if r == "admin":
            permissions = ["create", "edit", "view", "delete"]
        elif r == "editor":
            permissions = ["create", "edit", "view"]
        elif r == "viewer":
            permissions = ["view"]
        else:
            permissions = []
        return RoleOut(role=r or role, permissions=permissions, created_at=datetime.utcnow().isoformat())
