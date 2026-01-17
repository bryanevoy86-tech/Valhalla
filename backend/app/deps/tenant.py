from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from ..core.db import SessionLocal
from ..models.org import Org, OrgMember
from ..models.user import User
from .auth import get_current_user


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_org_id(
    x_org_id: str | None = Header(None),
    x_org_slug: str | None = Header(None),
    db: Session = Depends(get_db),
) -> int | None:
    if x_org_id:
        org = db.query(Org).get(int(x_org_id))
        if not org:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Org not found")
        return org.id
    if x_org_slug:
        org = db.query(Org).filter(Org.slug == x_org_slug).first()
        if not org:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Org not found")
        return org.id
    return None


def org_required(org_id: int | None = Depends(current_org_id)) -> int:
    if not org_id:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="X-Org-Id or X-Org-Slug required"
        )
    return org_id


def org_membership(required_roles: list[str] | None = None):
    required = set(required_roles or [])

    def _checker(
        org_id: int = Depends(org_required),
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        mem = (
            db.query(OrgMember)
            .filter(OrgMember.org_id == org_id, OrgMember.user_id == user.id)
            .first()
        )
        if not mem:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Not a member of this org")
        if required and mem.role not in required:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Insufficient org role")
        return {"org_id": org_id, "org_role": mem.role, "user": user}

    return _checker
