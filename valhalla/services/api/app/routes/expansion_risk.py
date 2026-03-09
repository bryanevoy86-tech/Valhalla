"""PACK 95: Expansion Risk & Compliance - Routes"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.expansion_risk import ExpansionRiskRuleCreate, ExpansionRiskRuleOut, ExpansionComplianceCreate, ExpansionComplianceOut
from app.services import expansion_risk_service

router = APIRouter(
    prefix="/expansion-risk",
    tags=["expansion_risk"]
)


# Risk rule endpoints
@router.post("/rule", response_model=ExpansionRiskRuleOut)
def create_risk_rule(rule: ExpansionRiskRuleCreate, db: Session = Depends(get_db)):
    return expansion_risk_service.create_risk_rule(db, rule)


@router.get("/rule/{rule_id}", response_model=ExpansionRiskRuleOut)
def get_risk_rule(rule_id: int, db: Session = Depends(get_db)):
    return expansion_risk_service.get_risk_rule(db, rule_id)


@router.get("/rule", response_model=list[ExpansionRiskRuleOut])
def list_risk_rules(zone_id: int | None = None, db: Session = Depends(get_db)):
    return expansion_risk_service.list_risk_rules(db, zone_id)


@router.delete("/rule/{rule_id}")
def delete_risk_rule(rule_id: int, db: Session = Depends(get_db)):
    success = expansion_risk_service.delete_risk_rule(db, rule_id)
    return {"deleted": success}


# Compliance check endpoints
@router.post("/compliance", response_model=ExpansionComplianceOut)
def create_compliance(check: ExpansionComplianceCreate, db: Session = Depends(get_db)):
    return expansion_risk_service.create_compliance_check(db, check)


@router.get("/compliance/{check_id}", response_model=ExpansionComplianceOut)
def get_compliance(check_id: int, db: Session = Depends(get_db)):
    return expansion_risk_service.get_compliance_check(db, check_id)


@router.get("/compliance", response_model=list[ExpansionComplianceOut])
def list_compliance_checks(zone_id: int | None = None, db: Session = Depends(get_db)):
    return expansion_risk_service.list_compliance_checks(db, zone_id)


@router.put("/compliance/{check_id}", response_model=ExpansionComplianceOut)
def update_compliance(check_id: int, check: ExpansionComplianceCreate, db: Session = Depends(get_db)):
    return expansion_risk_service.update_compliance_check(db, check_id, check)


@router.delete("/compliance/{check_id}")
def delete_compliance(check_id: int, db: Session = Depends(get_db)):
    success = expansion_risk_service.delete_compliance_check(db, check_id)
    return {"deleted": success}
