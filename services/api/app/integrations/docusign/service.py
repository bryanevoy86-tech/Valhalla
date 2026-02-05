"""DocuSign service - business logic for contract signing."""
from app.integrations.docusign.client import send_envelope, get_envelope_status


def execute_signature(contract, recipient_email: str) -> dict:
    """
    Execute signature workflow for a contract.
    
    Args:
        contract: Contract model instance
        recipient_email: Email of the person signing
    
    Returns:
        dict with envelope info
    """
    return send_envelope(
        contract_id=contract.id,
        recipient_email=recipient_email,
        document_url=f"/contracts/{contract.id}.pdf"
    )


def check_signature_status(envelope_id: str) -> dict:
    """Check if signature is complete."""
    return get_envelope_status(envelope_id)


def handle_signature_completion(envelope_id: str, contract_id: str) -> dict:
    """
    Handle webhook when signature is complete.
    
    Called by DocuSign webhook handler.
    """
    return {
        "envelope_id": envelope_id,
        "contract_id": contract_id,
        "status": "completed",
        "message": "Signature workflow complete"
    }
