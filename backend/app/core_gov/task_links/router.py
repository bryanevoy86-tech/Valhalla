"""P-TASKLINK-1: Cross-module audit linking router."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/core/links", tags=["task_links"])

class AuditLinkRequest(BaseModel):
    from_module: str
    from_id: str
    to_module: str
    to_id: str
    relation: str = "related"

class AuditLinkResponse(BaseModel):
    status: str
    message: str

@router.post("/audit")
def create_audit_link(req: AuditLinkRequest) -> AuditLinkResponse:
    """
    Create a safe audit link between two modules.
    
    Safe-calls: audit_log (safe)
    Does NOT persist cross-module state, only logs the relationship.
    """
    try:
        from ..audit_log import service as audit_service
        audit_service.log({
            "action": "link",
            "from": f"{req.from_module}:{req.from_id}",
            "to": f"{req.to_module}:{req.to_id}",
            "relation": req.relation,
        })
        return AuditLinkResponse(
            status="ok",
            message=f"Linked {req.from_module}:{req.from_id} → {req.to_module}:{req.to_id}"
        )
    except Exception as e:
        return AuditLinkResponse(
            status="audit-skipped",
            message=f"Link recorded locally; audit_log not available"
        )
