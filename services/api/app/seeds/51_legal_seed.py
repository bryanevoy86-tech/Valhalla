"""
Pack 51: Legal Document Engine - Seed starter variables, clause, and template
"""
from sqlalchemy.orm import Session
from app.legal.models import LegalVariable, LegalClause, LegalTemplate, LegalTemplateVersion


def run(db: Session):
    vars = [
        ("company_name", "Your legal company name", True, "Valhalla Legacy Inc"),
        ("company_address", "Registered address", True, "123 Main St, Winnipeg, MB"),
        ("counterparty_name", "Other party name", True, "Seller Name"),
        ("counterparty_address", "Other party address", False, "456 Oak Ave, City"),
        ("purchase_price", "Dollar amount numbers only", True, "250000"),
        ("closing_date", "ISO date", True, "2025-12-31"),
        ("property_address", "Subject property", True, "789 Elm St, City"),
        ("clause:As-Is Property", "Embed the 'As-Is' clause by name", False, ""),
    ]
    for k, d, r, e in vars:
        if not db.query(LegalVariable).filter_by(key=k).first():
            db.add(LegalVariable(key=k, desc=d, required=r, example=e))

    if not db.query(LegalClause).filter_by(name="As-Is Property").first():
        db.add(
            LegalClause(
                name="As-Is Property",
                jurisdiction="CA-MB",
                body="Buyer accepts the Property in 'as-is, where-is' condition, without representations or warranties.",
            )
        )

    t = db.query(LegalTemplate).filter_by(name="Wholesale Assignment").first()
    if not t:
        t = LegalTemplate(name="Wholesale Assignment", jurisdiction="CA-MB", kind="contract", active=True)
        db.add(t)
        db.commit()
        db.refresh(t)

    if not db.query(LegalTemplateVersion).filter_by(template_id=t.id, version=1).first():
        body = (
            "ASSIGNMENT OF CONTRACT\n\n"
            "Assignor: {{company_name}}, {{company_address}}\n"
            "Assignee: {{counterparty_name}}, {{counterparty_address}}\n"
            "Property: {{property_address}}\n"
            "Purchase Price: ${{purchase_price}}\n"
            "Closing: {{closing_date}}\n\n"
            "{{clause:As-Is Property}}\n\n"
            "Signed on {{closing_date}} by {{company_name}} and {{counterparty_name}}."
        )
        db.add(LegalTemplateVersion(template_id=t.id, version=1, body=body))
    db.commit()
    print("✅ Pack 51: Legal seed loaded")
