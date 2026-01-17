from fastapi import APIRouter

from app.roles.service import RolesService
from app.roles.schemas import RoleOut


router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/{role}", response_model=RoleOut)
async def get_role_permissions(role: str):
    return RolesService.get_role_permissions(role)
