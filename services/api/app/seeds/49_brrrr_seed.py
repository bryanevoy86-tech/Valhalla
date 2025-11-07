"""
Pack 49: Global BRRRR Zone Compliance Profiles
Seed sample jurisdictions (CA, BS, PA, PH, NZ) with rules, documents, taxes, and risk flags
"""
import os
from sqlalchemy.orm import Session
from app.brrrr.models import Jurisdiction, ComplianceRule, RequiredDocument, TaxBand, RiskFlag
import json


def seed_brrrr(db: Session) -> None:
    """
    Seed sample BRRRR compliance zones with rules, checklists, and tax bands.
    """
    # Jurisdictions
    zones = [
        {
            "zone_code": "CA",
            "zone_name": "California",
            "country_code": "US",
            "region": "West Coast",
            "currency": "USD",
            "notes": "High regulation, Prop 13 limits"
        },
        {
            "zone_code": "BS",
            "zone_name": "Bahamas",
            "country_code": "BS",
            "region": "Caribbean",
            "currency": "BSD",
            "notes": "Foreign ownership friendly, stamp duty applies"
        },
        {
            "zone_code": "PA",
            "zone_name": "Panama",
            "country_code": "PA",
            "region": "Central America",
            "currency": "USD",
            "notes": "Title insurance required, low property tax"
        },
        {
            "zone_code": "PH",
            "zone_name": "Philippines",
            "country_code": "PH",
            "region": "Southeast Asia",
            "currency": "PHP",
            "notes": "Foreign ownership restricted to condos, 60% Filipino ownership required for land"
        },
        {
            "zone_code": "NZ",
            "zone_name": "New Zealand",
            "country_code": "NZ",
            "region": "Oceania",
            "currency": "NZD",
            "notes": "Foreign buyer restrictions (OIO approval needed), bright-line test applies"
        }
    ]

    for z in zones:
        existing = db.query(Jurisdiction).filter_by(zone_code=z["zone_code"]).first()
        if not existing:
            jurisdiction = Jurisdiction(**z)
            db.add(jurisdiction)

    db.commit()

    # Compliance Rules
    rules = [
        {"zone_code": "CA", "rule_key": "max_ltv", "rule_value": "80", "applies_to_deal_types": json.dumps(["BRRRR", "wholesale"]), "severity": "warning"},
        {"zone_code": "BS", "rule_key": "stamp_duty", "rule_value": "10", "applies_to_deal_types": None, "severity": "info"},
        {"zone_code": "PA", "rule_key": "title_insurance", "rule_value": "mandatory", "applies_to_deal_types": json.dumps(["BRRRR"]), "severity": "error"},
        {"zone_code": "PH", "rule_key": "foreign_ownership", "rule_value": "condo_only", "applies_to_deal_types": None, "severity": "error"},
        {"zone_code": "NZ", "rule_key": "OIO_approval", "rule_value": "required", "applies_to_deal_types": json.dumps(["BRRRR"]), "severity": "error"}
    ]

    for r in rules:
        existing = db.query(ComplianceRule).filter_by(zone_code=r["zone_code"], rule_key=r["rule_key"]).first()
        if not existing:
            rule = ComplianceRule(**r)
            db.add(rule)

    db.commit()

    # Required Documents
    docs = [
        {"zone_code": "CA", "deal_type": "BRRRR", "doc_name": "Purchase Agreement", "doc_category": "contract", "is_mandatory": True},
        {"zone_code": "CA", "deal_type": "BRRRR", "doc_name": "Title Report", "doc_category": "due_diligence", "is_mandatory": True},
        {"zone_code": "BS", "deal_type": "BRRRR", "doc_name": "Stamp Duty Payment", "doc_category": "tax", "is_mandatory": True},
        {"zone_code": "PA", "deal_type": "BRRRR", "doc_name": "Title Insurance Policy", "doc_category": "insurance", "is_mandatory": True},
        {"zone_code": "PH", "deal_type": "BRRRR", "doc_name": "Condominium Certificate of Title", "doc_category": "ownership", "is_mandatory": True},
        {"zone_code": "NZ", "deal_type": "BRRRR", "doc_name": "OIO Application", "doc_category": "regulatory", "is_mandatory": True, "description": "Overseas Investment Office approval for foreign buyers"}
    ]

    for d in docs:
        existing = db.query(RequiredDocument).filter_by(zone_code=d["zone_code"], deal_type=d["deal_type"], doc_name=d["doc_name"]).first()
        if not existing:
            doc = RequiredDocument(**d)
            db.add(doc)

    db.commit()

    # Tax Bands
    taxes = [
        {"zone_code": "CA", "tax_type": "transfer_tax", "min_value": 0, "max_value": 1000000, "rate_pct": 0.55, "flat_fee": 0},
        {"zone_code": "CA", "tax_type": "transfer_tax", "min_value": 1000000, "max_value": None, "rate_pct": 1.1, "flat_fee": 0},
        {"zone_code": "BS", "tax_type": "stamp_duty", "min_value": 0, "max_value": None, "rate_pct": 10.0, "flat_fee": 0},
        {"zone_code": "PA", "tax_type": "property_tax", "min_value": 0, "max_value": None, "rate_pct": 0.5, "flat_fee": 0},
        {"zone_code": "PH", "tax_type": "capital_gains", "min_value": 0, "max_value": None, "rate_pct": 6.0, "flat_fee": 0},
        {"zone_code": "NZ", "tax_type": "brightline_test", "min_value": 0, "max_value": None, "rate_pct": 33.0, "flat_fee": 0, "description": "Applies if sold within 10 years"}
    ]

    for t in taxes:
        existing = db.query(TaxBand).filter_by(zone_code=t["zone_code"], tax_type=t["tax_type"], min_value=t["min_value"]).first()
        if not existing:
            tax = TaxBand(**t)
            db.add(tax)

    db.commit()

    # Risk Flags
    flags = [
        {"zone_code": "BS", "flag_name": "Foreign Buyer", "condition": "foreign_owner", "risk_impact": "medium", "description": "Higher stamp duty for non-residents"},
        {"zone_code": "PH", "flag_name": "Land Ownership Restricted", "condition": "foreign_owner", "risk_impact": "high", "description": "Foreigners cannot own land, only condos"},
        {"zone_code": "NZ", "flag_name": "OIO Required", "condition": "foreign_owner", "risk_impact": "high", "description": "OIO approval mandatory for foreign buyers"}
    ]

    for f in flags:
        existing = db.query(RiskFlag).filter_by(zone_code=f["zone_code"], flag_name=f["flag_name"]).first()
        if not existing:
            flag = RiskFlag(**f)
            db.add(flag)

    db.commit()
    print("✅ Pack 49: Global BRRRR Zone Compliance seeded (CA, BS, PA, PH, NZ)")
