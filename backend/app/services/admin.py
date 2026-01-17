from typing import Any, Dict, Optional

from app.models.feature_flag import AdminAction, FeatureFlag
from app.models.user import User
from sqlalchemy.orm import Session


def log_admin(
    db: Session,
    *,
    actor_user_id: Optional[int],
    org_id: Optional[int],
    action: str,
    details: Dict[str, Any] | None = None,
):
    db.add(
        AdminAction(
            actor_user_id=actor_user_id, org_id=org_id, action=action, details=details or {}
        )
    )
    db.commit()


def set_feature_flag(
    db: Session,
    *,
    scope: str,
    key: str,
    enabled: bool,
    payload: dict | None = None,
    org_id: int | None = None,
    user_id: int | None = None,
):
    q = db.query(FeatureFlag).filter(FeatureFlag.key == key, FeatureFlag.scope == scope)
    if scope == "org":
        q = q.filter(FeatureFlag.org_id == org_id)
    if scope == "user":
        q = q.filter(FeatureFlag.user_id == user_id)
    row = q.first()
    if not row:
        row = FeatureFlag(
            scope=scope, key=key, enabled=enabled, payload=payload, org_id=org_id, user_id=user_id
        )
        db.add(row)
    else:
        row.enabled = enabled
        row.payload = payload
    db.commit()
    db.refresh(row)
    return row


def list_feature_flags(db: Session, *, org_id: int | None = None, user_id: int | None = None):
    q = db.query(FeatureFlag)
    if org_id is not None:
        q = q.filter(
            (FeatureFlag.scope == "global")
            | ((FeatureFlag.scope == "org") & (FeatureFlag.org_id == org_id))
            | ((FeatureFlag.scope == "user") & (FeatureFlag.user_id == user_id))
        )
    return q.order_by(FeatureFlag.key.asc()).all()


def promote_user_role(db: Session, *, user_id: int, role: str):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        return None
    u.role = role
    db.commit()
    return u
