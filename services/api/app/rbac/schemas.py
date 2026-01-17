"""
Pydantic schemas for RBAC operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Role Schemas
class RoleCreate(BaseModel):
    role_name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class RoleOut(BaseModel):
    role_id: int
    role_name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Permission Schemas
class PermissionCreate(BaseModel):
    permission_name: str = Field(..., min_length=1, max_length=100)
    resource: Optional[str] = None
    action: Optional[str] = None
    description: Optional[str] = None


class PermissionOut(BaseModel):
    permission_id: int
    permission_name: str
    resource: Optional[str] = None
    action: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Role-Permission Assignment Schemas
class RolePermissionAssign(BaseModel):
    role_name: str
    permission_name: str


class RolePermissionOut(BaseModel):
    role_id: int
    permission_id: int
    assigned_at: datetime

    class Config:
        from_attributes = True


# User-Role Assignment Schemas
class UserRoleAssign(BaseModel):
    user_id: int
    role_name: str
    assigned_by: Optional[int] = None


class UserRoleOut(BaseModel):
    user_id: int
    role_id: int
    assigned_at: datetime
    assigned_by: Optional[int] = None

    class Config:
        from_attributes = True


# Combined Schemas
class RoleWithPermissions(BaseModel):
    role: RoleOut
    permissions: List[PermissionOut]


class UserWithRoles(BaseModel):
    user_id: int
    roles: List[RoleOut]


class PermissionCheck(BaseModel):
    user_id: int
    permission_name: str
    has_permission: bool
    granted_by_roles: List[str] = []
