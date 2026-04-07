from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.alerting import AlertChannel, AlertRule
from app.schemas.alerting import (
    AlertChannelCreate,
    AlertChannelOut,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleOut,
)

router = APIRouter()


@router.post("/channels", response_model=AlertChannelOut)
def create_alert_channel(
    payload: AlertChannelCreate,
    db: Session = Depends(get_db),
):
    obj = AlertChannel(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/channels", response_model=list[AlertChannelOut])
def list_alert_channels(
    active: bool | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(AlertChannel)
    if active is not None:
        query = query.filter(AlertChannel.active == active)
    return query.all()


@router.post("/rules", response_model=AlertRuleOut)
def create_alert_rule(
    payload: AlertRuleCreate,
    db: Session = Depends(get_db),
):
    obj = AlertRule(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/rules", response_model=list[AlertRuleOut])
def list_alert_rules(
    event_type: str | None = None,
    active: bool | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(AlertRule)
    if event_type:
        query = query.filter(AlertRule.event_type == event_type)
    if active is not None:
        query = query.filter(AlertRule.active == active)
    return query.all()


@router.put("/rules/{rule_id}", response_model=AlertRuleOut)
def update_alert_rule(
    rule_id: int,
    payload: AlertRuleUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(AlertRule).get(rule_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
