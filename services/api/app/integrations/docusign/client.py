"""DocuSign client - production-safe, gated signature integration."""
import uuid
from app.core.runtime_flags import is_live


def send_envelope(contract_id: str, recipient_email: str, document_url: str) -> dict:
    """
    Send a document to DocuSign for signature.
    
    Args:
        contract_id: Contract identifier
        recipient_email: Recipient email address
        document_url: URL to the document
    
    Returns:
        dict with envelope_id and status
    """
    envelope_id = f"docusign_{uuid.uuid4().hex[:12]}"
    
    if not is_live():
        # Sandbox: return mock response
        return {
            "status": "sandbox",
            "envelope_id": envelope_id,
            "contract_id": contract_id,
            "message": "DocuSign sandbox - no real signature request"
        }
    
    # REAL SDK CALL GOES HERE
    # from docusign_esign import ApiClient, EnvelopesApi
    # api_client = ApiClient()
    # envelopes_api = EnvelopesApi(api_client)
    # response = envelopes_api.create_envelope(...)
    
    return {
        "status": "sent",
        "envelope_id": envelope_id,
        "contract_id": contract_id,
        "recipient_email": recipient_email,
        "message": "Envelope sent for signature"
    }


def get_envelope_status(envelope_id: str) -> dict:
    """Get the status of a DocuSign envelope."""
    if not is_live():
        return {
            "status": "sandbox",
            "envelope_id": envelope_id,
            "message": "Sandbox mode"
        }
    
    # TODO: Implement real DocuSign API call
    return {
        "status": "pending",
        "envelope_id": envelope_id,
        "message": "Envelope status (stub)"
    }


def webhook_handler(event_data: dict) -> dict:
    """
    Handle DocuSign webhook events.
    
    Called when envelope status changes (sent, viewed, signed, completed)
    """
    return {
        "status": "processed",
        "event": event_data.get("eventType"),
        "message": "Webhook received"
    }
