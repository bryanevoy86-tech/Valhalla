"""
Pack 49: Global BRRRR Zone Compliance Profiles
Service layer for zone evaluation, checklist generation, and tax calculation
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.brrrr.models import Jurisdiction, ComplianceRule, RequiredDocument, TaxBand, ComplianceEvent, RiskFlag
from app.brrrr.schemas import EvaluateIn, EvaluateOut, ChecklistItem, TaxEstimate
from decimal import Decimal
from typing import List, Optional
import json


def list_zones(db: Session) -> List[Jurisdiction]:
    """
    List all registered jurisdictions.
    """
    return db.query(Jurisdiction).order_by(Jurisdiction.zone_code).all()


def get_checklist(db: Session, zone: str, deal_type: str) -> List[RequiredDocument]:
    """
    Get required document checklist for a zone and deal type.
    """
    return (
        db.query(RequiredDocument)
        .filter(and_(RequiredDocument.zone_code == zone, RequiredDocument.deal_type == deal_type))
        .order_by(RequiredDocument.is_mandatory.desc(), RequiredDocument.doc_name)
        .all()
    )


def evaluate(db: Session, req: EvaluateIn) -> EvaluateOut:
    """
    Evaluate compliance for a deal in a given zone.
    Returns ok/warnings/risk_score/checklist/taxes.
    """
    warnings = []
    risk_score = 0.0

    # Check if zone exists
    jurisdiction = db.query(Jurisdiction).filter_by(zone_code=req.zone).first()
    if not jurisdiction:
        return EvaluateOut(
            ok=False,
            warnings=[f"Zone {req.zone} not found"],
            risk_score=100.0,
            checklist=[],
            taxes=[],
            notes="Invalid zone code"
        )

    # Get compliance rules
    rules = (
        db.query(ComplianceRule)
        .filter(ComplianceRule.zone_code == req.zone)
        .all()
    )
    for rule in rules:
        # Check if rule applies to this deal type
        if rule.applies_to_deal_types:
            deal_types = json.loads(rule.applies_to_deal_types)
            if req.deal_type not in deal_types:
                continue
        
        # Simple rule evaluation (example: LTV limits)
        if rule.rule_key == "max_ltv" and req.ltv is not None:
            max_ltv = float(rule.rule_value)
            if req.ltv > max_ltv:
                warnings.append(f"LTV {req.ltv}% exceeds {rule.rule_key} limit of {max_ltv}%")
                risk_score += 10.0 if rule.severity == "error" else 5.0

    # Check risk flags
    flags = db.query(RiskFlag).filter_by(zone_code=req.zone).all()
    for flag in flags:
        # Simple condition checks
        if flag.condition == "foreign_owner" and req.foreign_owner:
            warnings.append(f"Risk flag: {flag.flag_name}")
            if flag.risk_impact == "high":
                risk_score += 15.0
            elif flag.risk_impact == "medium":
                risk_score += 8.0
            else:
                risk_score += 3.0

    # Get checklist
    docs = get_checklist(db, req.zone, req.deal_type)
    checklist = [
        ChecklistItem(
            doc_name=doc.doc_name,
            doc_category=doc.doc_category,
            is_mandatory=doc.is_mandatory,
            description=doc.description
        )
        for doc in docs
    ]

    # Calculate taxes
    taxes = _calculate_taxes(db, req.zone, req.purchase_price)

    ok = len(warnings) == 0 or all(w.startswith("Risk flag:") for w in warnings)

    # Log compliance event
    event = ComplianceEvent(
        zone_code=req.zone,
        deal_type=req.deal_type,
        result="ok" if ok else "warning",
        warnings=json.dumps(warnings),
        risk_score=risk_score,
        snapshot_json=json.dumps(req.model_dump(), default=str)
    )
    db.add(event)
    db.commit()

    return EvaluateOut(
        ok=ok,
        warnings=warnings,
        risk_score=risk_score,
        checklist=checklist,
        taxes=taxes,
        notes=jurisdiction.notes
    )


def _calculate_taxes(db: Session, zone: str, value: Decimal) -> List[TaxEstimate]:
    """
    Calculate applicable taxes based on tax bands.
    """
    taxes = []
    bands = db.query(TaxBand).filter_by(zone_code=zone).order_by(TaxBand.tax_type, TaxBand.min_value).all()
    
    # Group by tax_type
    by_type = {}
    for band in bands:
        if band.tax_type not in by_type:
            by_type[band.tax_type] = []
        by_type[band.tax_type].append(band)
    
    for tax_type, type_bands in by_type.items():
        # Find applicable band
        for band in type_bands:
            if band.min_value <= value and (band.max_value is None or value <= band.max_value):
                total = value * (band.rate_pct / Decimal(100)) + band.flat_fee
                taxes.append(
                    TaxEstimate(
                        tax_type=tax_type,
                        base_value=value,
                        rate_pct=float(band.rate_pct),
                        flat_fee=band.flat_fee,
                        total=total
                    )
                )
                break
    
    return taxes
