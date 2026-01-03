from fastapi import APIRouter, Depends
from ..config.thresholds import Thresholds, load_thresholds, save_thresholds
from ..audit.audit_log import audit
from ..security.rbac import require_scopes, require_active_subscription
from ..security.devkey.deps import require_dev_key
from ..rate_limit.deps import rate_limit

router = APIRouter(prefix="/config", tags=["Core: Config"])

@router.get("/thresholds", response_model=Thresholds)
def get_thresholds():
    return load_thresholds()

@router.post("/thresholds", response_model=Thresholds)
def set_thresholds(
    payload: Thresholds,
    _key=Depends(require_dev_key),
    _sub=Depends(require_active_subscription),
    _owner=require_scopes("owner"),
    _rl=rate_limit("thresholds_set", max_requests=5, window_seconds=60),
):
    save_thresholds(payload)
    audit("THRESHOLDS_SET", payload.model_dump())
    return payload
