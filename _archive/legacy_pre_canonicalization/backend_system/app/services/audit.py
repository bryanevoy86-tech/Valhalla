from typing import Any, Dict

from backend.app.models.audit_log import AuditLog
from sqlalchemy.orm import Session

MASK_KEYS = {"password", "secret", "token", "hash", "salt", "ssn", "credit_card"}


def _mask(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        return "***" if len(value) > 0 else value
    if isinstance(value, (list, tuple)):
        return [_mask(v) for v in value]
    if isinstance(value, dict):
        return {k: (_mask(v) if k.lower() not in MASK_KEYS else "***") for k, v in value.items()}
    return value


def model_to_dict(obj, drop: set[str] | None = None) -> Dict[str, Any]:
    drop = drop or set()
    out = {}
    for c in obj.__table__.columns:
        if c.name in drop:
            continue
        out[c.name] = getattr(obj, c.name)
    return out


def json_diff(before: Dict[str, Any] | None, after: Dict[str, Any] | None) -> Dict[str, Any]:
    before = before or {}
    after = after or {}
    changed = {
        k: [before[k], after[k]] for k in before.keys() & after.keys() if before[k] != after[k]
    }
    added = {k: after[k] for k in after.keys() - before.keys()}
    removed = list(before.keys() - after.keys())
    return {"changed": changed, "added": added, "removed": removed}


def log_audit(
    db: Session,
    *,
    org_id: int | None,
    actor_user_id: int | None,
    action: str,
    entity: str,
    entity_id: str | None,
    before: Dict[str, Any] | None = None,
    after: Dict[str, Any] | None = None,
    request_id: str | None = None,
    route: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    meta: Dict[str, Any] | None = None,
) -> int:
    row = AuditLog(
        org_id=org_id,
        actor_user_id=actor_user_id,
        action=action,
        entity=entity,
        entity_id=(str(entity_id) if entity_id is not None else None),
        before=_mask(before),
        after=_mask(after),
        request_id=request_id,
        route=route,
        ip=ip,
        user_agent=user_agent,
        meta=meta or {},
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row.id
