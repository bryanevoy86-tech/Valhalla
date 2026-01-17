"""PACK 95: Expansion Risk & Compliance - Service"""

from sqlalchemy.orm import Session

from app.models.expansion_risk import ExpansionRiskRule, ExpansionComplianceCheck
from app.schemas.expansion_risk import ExpansionRiskRuleCreate, ExpansionComplianceCreate


# Expansion risk rule operations
def create_risk_rule(db: Session, rule: ExpansionRiskRuleCreate) -> ExpansionRiskRule:
    db_rule = ExpansionRiskRule(
        zone_id=rule.zone_id,
        rule_name=rule.rule_name,
        risk_payload=rule.risk_payload
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


def list_risk_rules(db: Session, zone_id: int | None = None) -> list[ExpansionRiskRule]:
    q = db.query(ExpansionRiskRule)
    if zone_id:
        q = q.filter(ExpansionRiskRule.zone_id == zone_id)
    return q.order_by(ExpansionRiskRule.id.desc()).all()


def get_risk_rule(db: Session, rule_id: int) -> ExpansionRiskRule | None:
    return db.query(ExpansionRiskRule).filter(ExpansionRiskRule.id == rule_id).first()


def delete_risk_rule(db: Session, rule_id: int) -> bool:
    db_rule = get_risk_rule(db, rule_id)
    if not db_rule:
        return False
    db.delete(db_rule)
    db.commit()
    return True


# Expansion compliance check operations
def create_compliance_check(db: Session, check: ExpansionComplianceCreate) -> ExpansionComplianceCheck:
    db_check = ExpansionComplianceCheck(
        zone_id=check.zone_id,
        status=check.status,
        notes=check.notes
    )
    db.add(db_check)
    db.commit()
    db.refresh(db_check)
    return db_check


def list_compliance_checks(db: Session, zone_id: int | None = None) -> list[ExpansionComplianceCheck]:
    q = db.query(ExpansionComplianceCheck)
    if zone_id:
        q = q.filter(ExpansionComplianceCheck.zone_id == zone_id)
    return q.order_by(ExpansionComplianceCheck.id.desc()).all()


def get_compliance_check(db: Session, check_id: int) -> ExpansionComplianceCheck | None:
    return db.query(ExpansionComplianceCheck).filter(ExpansionComplianceCheck.id == check_id).first()


def update_compliance_check(db: Session, check_id: int, check: ExpansionComplianceCreate) -> ExpansionComplianceCheck | None:
    db_check = get_compliance_check(db, check_id)
    if not db_check:
        return None
    db_check.zone_id = check.zone_id
    db_check.status = check.status
    db_check.notes = check.notes
    db.commit()
    db.refresh(db_check)
    return db_check


def delete_compliance_check(db: Session, check_id: int) -> bool:
    db_check = get_compliance_check(db, check_id)
    if not db_check:
        return False
    db.delete(db_check)
    db.commit()
    return True
