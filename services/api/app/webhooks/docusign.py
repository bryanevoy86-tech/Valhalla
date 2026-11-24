"""Legacy DocuSign ingress remains disabled until Connect evidence is commissioned."""
from fastapi import APIRouter, HTTPException

from app.heimdall.authority import is_live

router = APIRouter(prefix="/webhooks/docusign")


@router.post("")
async def docusign_webhook():
    if not is_live():
        return {"status": "sandbox_ignored"}
    raise HTTPException(503, "DocuSign Connect authentication and scoped envelope evidence are not commissioned")
