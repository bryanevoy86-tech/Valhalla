# Pack 25: Role-Based Access Control (RBAC)

This pack adds database-backed Roles and Permissions with assignments to users, route-protection helpers, a full REST API, and an admin dashboard UI.

## Models
- Role(role_id, role_name, description, created_at)
- Permission(permission_id, permission_name, resource, action, description, created_at)
- RolePermission(role_id, permission_id, assigned_at)
- UserRole(user_id, role_id, assigned_at, assigned_by)

All tables are defined in `app/rbac/models.py` using SQLAlchemy. Cascade deletes clean up assignments.

## Schemas
Pydantic schemas in `app/rbac/schemas.py`: RoleCreate/Out, PermissionCreate/Out, RolePermissionAssign/Out, UserRoleAssign/Out, RoleWithPermissions, UserWithRoles, PermissionCheck.

## Service
`app/rbac/service.py` contains `RBACService` with:
- Role CRUD: create_role, get_role, get_role_by_name, list_roles, delete_role
- Permission CRUD: create_permission, get_permission, get_permission_by_name, list_permissions, delete_permission
- Role-Permission: assign_permission_to_role, remove_permission_from_role, get_role_permissions
- User-Role: assign_role_to_user, remove_role_from_user, get_user_roles
- Checks: user_has_permission, user_has_role, get_user_permissions, get_users_with_role
- Bootstrap: initialize_default_roles_and_permissions()

## API Router
- File: `app/routers/rbac.py`
- Base prefix: `/api/rbac`

Endpoints:
- Roles
  - POST `/roles` -> RoleOut
  - GET `/roles` -> List[RoleOut]
  - GET `/roles/{role_id}` -> RoleOut
  - GET `/roles/name/{role_name}` -> RoleOut
  - DELETE `/roles/{role_id}`
- Permissions
  - POST `/permissions` -> PermissionOut
  - GET `/permissions` -> List[PermissionOut]
  - GET `/permissions/{permission_id}` -> PermissionOut
  - DELETE `/permissions/{permission_id}`
- Role-Permission
  - POST `/role-permissions/assign` {role_name, permission_name}
  - POST `/role-permissions/remove` {role_name, permission_name}
  - GET `/role-permissions/{role_name}` -> RoleWithPermissions
- User-Role
  - POST `/user-roles/assign` {user_id, role_name, assigned_by?}
  - POST `/user-roles/remove?user_id=..&role_name=..`
  - GET `/user-roles/{user_id}` -> UserWithRoles
- Checks
  - GET `/check-permission/{user_id}/{permission_name}` -> PermissionCheck
  - GET `/check-role/{user_id}/{role_name}`
  - GET `/user-permissions/{user_id}` -> { permissions: [str] }
- Utility
  - POST `/initialize-defaults` (creates default roles/permissions and assignments)
  - GET `/users-with-role/{role_name}` -> { user_ids: [int] }

The router is conditionally registered in `services/api/main.py`; see RBAC_AVAILABLE flag in `/debug/routes`.

## Route Protection Middleware
`app/rbac/middleware.py` exposes dependency factories to protect routes via FastAPI Depends:

- require_role("admin")
- require_any_role(["admin", "manager"]) 
- require_permission("write:users")
- require_any_permission(["write:users", "write:content"]) 

Example usage:

```python
from fastapi import APIRouter, Depends
from app.rbac.middleware import RBACMiddleware

router = APIRouter(prefix="/secure")

@router.get("/admin-only", dependencies=[Depends(RBACMiddleware.require_role("admin"))])
async def admin_only():
    return {"ok": True}

@router.post("/edit-users", dependencies=[Depends(RBACMiddleware.require_permission("write:users"))])
async def edit_users():
    return {"ok": True}
```

Assumption: You provide a `user-x-id` header on requests to identify the current user. Adjust `RBACMiddleware._get_current_user_id` if your auth mechanism differs.

## UI Dashboard
- Path: `/api/ui-dashboard/rbac-dashboard-ui`
- Template: `app/ui_dashboard/templates/rbac_dashboard.html`
- Features:
  - Create/list/delete roles and permissions
  - Assign permissions to roles and view them
  - Assign roles to users and view/remove them
  - Check user permissions and list all permissions for a user
  - Initialize default roles and permissions

## Bootstrapping Defaults
Initialize a complete default setup:
- POST `/api/rbac/initialize-defaults`
  - Roles: admin, manager, user, viewer
  - Permissions: read/write/delete users/content, manage:roles, manage:permissions
  - Assignments: sensible defaults (admin gets all)

## Notes
- Works with existing user profiles (Pack 24) by using `user_id` in `UserRole`.
- SQLAlchemy types may trigger editor warnings; runtime behavior is correct. The router casts model attributes to strings for clarity.
- Tables auto-create at startup if `app.core.db` is available.
