from fastapi import Depends, Header, HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.db import SessionLocal
from ..models.user import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    token = _extract_bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    s = get_settings()
    try:
        payload = jwt.decode(token, s.SECRET_KEY, algorithms=["HS256"])
        sub = payload.get("sub")
        if not sub:
            raise ValueError("no sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def role_guard(roles: list[str]):
    def _guard(user: User = Depends(get_current_user)):
        if user.role not in roles:
            # Audit log for unauthorized role access
            from ..services.audit import log_event

            log_event(
                "unauthorized_role_access",
                user_id=user.id,
                details={"role": user.role, "required": roles},
            )
            raise HTTPException(status_code=403, detail="Forbidden: insufficient role")
        return user

    return _guard


def legacy_access_guard(legacy_id: str):
    def _guard(user: User = Depends(get_current_user)):
        import json

        legacies = json.loads(user.legacies or "[]")
        if legacy_id not in legacies and user.role != "admin":
            from ..services.audit import log_event

            log_event(
                "unauthorized_legacy_access",
                user_id=user.id,
                details={"legacy_id": legacy_id, "user_legacies": legacies},
            )
            raise HTTPException(status_code=403, detail="Forbidden: no access to this legacy")
        return user

    return _guard
