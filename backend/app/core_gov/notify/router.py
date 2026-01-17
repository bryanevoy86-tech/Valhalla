from fastapi import APIRouter, Depends

from ..notify.queue import list_all, clear_all
from ..security.rbac import require_scopes, require_active_subscription
from ..security.devkey.deps import require_dev_key
from ..rate_limit.deps import rate_limit

router = APIRouter(prefix="/notify", tags=["Core: Notify"])

@router.get("")
def read_notifications(limit: int = 50):
    return {"items": list_all(limit=limit)}

@router.post("/clear")
def clear_notifications(
    _key=Depends(require_dev_key),
    _sub=Depends(require_active_subscription),
    _owner=require_scopes("owner"),
    _rl=rate_limit("notify_clear", max_requests=10, window_seconds=60),
):
    return clear_all()
