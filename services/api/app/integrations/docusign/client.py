"""DocuSign client - production-safe, gated signature integration."""
import uuid

from fastapi import HTTPException

from app.integrations.commissioning import approved_reader, commissioning_receipt, read_json

from app.core.engines.actions import CONTRACT_SEND
from app.core.engines.guard_runtime import enforce_engine
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
    enforce_engine(
        "wholesaling",
        CONTRACT_SEND,
        {
            "provider": "docusign",
            "contract_id": contract_id,
            "target_type": "signature_envelope",
        },
    )
    envelope_id = f"docusign_{uuid.uuid4().hex[:12]}"
    
    if not is_live():
        # Sandbox: return mock response
        return {
            "status": "sandbox",
            "envelope_id": envelope_id,
            "contract_id": contract_id,
            "message": "DocuSign sandbox - no real signature request"
        }
    
    raise HTTPException(503, "DocuSign sending has not been commissioned")


def get_envelope_status(envelope_id: str) -> dict:
    """Inspect the exact DocuSign fixture envelope without sending or downloading it."""
    if not is_live() and envelope_id.startswith("docusign_"):
        return {"status": "sandbox", "envelope_id": envelope_id, "message": "Simulated envelope"}
    return read_envelope_fixture(envelope_id=envelope_id)


def read_envelope_fixture(*, envelope_id=None, transport=None):
    with approved_reader("DOCUSIGN", "https://demo.docusign.net", "ACCOUNT_ID", "ENVELOPE_ID", "SIGNER_EMAIL",
                         transport=transport) as (client, config):
        account, reference, email = config
        try:
            if any(str(uuid.UUID(value)) != value for value in (account, reference)):
                raise ValueError
        except ValueError:
            raise HTTPException(503, "Exact DocuSign test account and envelope configuration required") from None
        if envelope_id is not None and envelope_id != reference:
            raise HTTPException(409, "Envelope differs from the approved commissioning scope")
        path = f"/restapi/v2.1/accounts/{account}/envelopes/{reference}"
        envelope = read_json(client, path)
        status = envelope.get("status")
        if envelope.get("envelopeId") != reference or status not in {
            "created", "sent", "delivered", "completed", "declined", "voided",
        }:
            raise HTTPException(409, "DocuSign envelope evidence did not match the configured resource")
        recipients = read_json(client, path + "/recipients")
        signers = recipients.get("signers")
        if (not isinstance(signers, list) or len(signers) != 1 or not isinstance(signers[0], dict)
                or not isinstance(signers[0].get("email"), str) or signers[0]["email"].casefold() != email.casefold()
                or str(recipients.get("recipientCount")) != "1"
                or (status == "completed" and signers[0].get("status") != "completed")):
            raise HTTPException(409, "DocuSign test signer or completed status did not reconcile")
    return commissioning_receipt("DOCUSIGN", f"{account}/{reference}", envelope_status=status,
                                 document_downloaded=False, legal_reliance_authorized=False)
