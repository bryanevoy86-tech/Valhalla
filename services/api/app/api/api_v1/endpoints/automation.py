from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.automation_rule import AutomationRule
from app.schemas.automation import (
    AutomationRuleCreate,
    AutomationRuleUpdate,
    AutomationRuleOut,
)

router = APIRouter()


@router.post("/", response_model=AutomationRuleOut)
def create_automation_rule(payload: AutomationRuleCreate, db: Session = Depends(get_db)):
    obj = AutomationRule(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[AutomationRuleOut])
def list_automation_rules(category: str | None = None, active: bool | None = None, db: Session = Depends(get_db)):
    query = db.query(AutomationRule)
    if category:
        query = query.filter(AutomationRule.category == category)
    if active is not None:
        query = query.filter(AutomationRule.active == active)
    return query.all()


@router.put("/{rule_id}", response_model=AutomationRuleOut)
def update_automation_rule(rule_id: int, payload: AutomationRuleUpdate, db: Session = Depends(get_db)):
    obj = db.query(AutomationRule).get(rule_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
