"""
Module 37: DocuSign Webhook Handler
Handles incoming webhook events from DocuSign (envelope status updates).
"""
from fastapi import APIRouter, Request
from app.heimdall.authority import is_live

router = APIRouter(prefix="/webhooks/docusign")


@router.post("")
async def docusign_webhook(req: Request):
    """
    Handle DocuSign webhook events.
    
    Supported statuses:
    - completed: All parties have signed
    - sent: Envelope sent to signers
    - declined: Signer declined
    - voided: Envelope voided
    """
    if not is_live():
        return {"status": "sandbox_ignored"}
    
    try:
        payload = await req.json()
        
        # DocuSign sends envelope status data
        envelope_status = payload.get("status")
        envelope_id = payload.get("envelope_id")
        
        if envelope_status == "completed":
            # All parties signed - contract is executable
            return {
                "contract": "signed",
                "status": "completed",
                "envelope_id": envelope_id,
                "action": "mark_contract_executable"
            }

        elif envelope_status == "sent":
            # Envelope sent to signers
            return {
                "status": "sent",
                "envelope_id": envelope_id,
                "action": "update_contract_sent"
            }

        elif envelope_status == "declined":
            # Signer declined - contract failed
            return {
                "status": "declined",
                "envelope_id": envelope_id,
                "action": "mark_contract_failed"
            }

        elif envelope_status == "voided":
            # Envelope voided
            return {
                "status": "voided",
                "envelope_id": envelope_id,
                "action": "mark_contract_voided"
            }

        return {
            "status": "pending",
            "envelope_id": envelope_id,
            "envelope_status": envelope_status
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
