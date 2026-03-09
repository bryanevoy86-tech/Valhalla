"""Contract PDF generation pipeline."""
from app.storage.s3 import upload_document


def generate_contract_pdf(contract):
    """Generate contract PDF and upload to S3."""
    # In real implementation, use reportlab or similar to generate PDF
    pdf_content = f"""
    CONTRACT {contract.get('id', 'unknown')}
    
    Template: {contract.get('template_id', 'unknown')}
    State: {contract.get('state', 'DRAFT')}
    Created: {contract.get('created_at', 'unknown')}
    """
    
    key = f"contracts/{contract.get('id')}.pdf"
    return upload_document(key, pdf_content)


def regenerate_contract(contract_id, contract_data):
    """Regenerate contract PDF with updated data."""
    return generate_contract_pdf(contract_data)


def get_contract_pdf_url(contract_id):
    """Get S3 URL for contract PDF."""
    return {
        "contract_id": contract_id,
        "pdf_url": f"s3://valhalla/contracts/{contract_id}.pdf"
    }
