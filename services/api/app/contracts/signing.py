"""Contract signing orchestration."""
from app.integrations.docusign.service import execute_signature
from app.contracts.generator import generate_contract_pdf
from app.contracts.audit import audit_sent, audit_signed


def start_signing(contract, recipient_email):
    """Start the signing process for a contract."""
    # Step 1: Generate PDF
    pdf_result = generate_contract_pdf(contract)
    
    if not pdf_result.get("url"):
        return {
            "status": "error",
            "message": "Failed to generate PDF"
        }
    
    # Step 2: Audit that contract was sent
    audit_sent(contract.get("id"), recipient_email)
    
    # Step 3: Send to DocuSign
    sig_result = execute_signature(
        contract_id=contract.get("id"),
        recipient_email=recipient_email,
        document_url=pdf_result.get("url")
    )
    
    return {
        "status": "sent",
        "contract_id": contract.get("id"),
        "envelope_id": sig_result.get("envelope_id"),
        "recipient": recipient_email
    }


def complete_signing(contract_id, envelope_id):
    """Complete signing process when envelope is signed."""
    from app.contracts.audit import audit_signed
    
    audit_signed(contract_id, f"docusign_{envelope_id}")
    
    return {
        "status": "completed",
        "contract_id": contract_id,
        "envelope_id": envelope_id
    }
