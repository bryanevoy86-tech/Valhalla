from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from app.models.funfund import Disbursement, FundingRequest, Repayment
from sqlalchemy.orm import Session


def compute_balance(db: Session, request_id: int) -> Dict[str, Any]:
    req = db.query(FundingRequest).filter(FundingRequest.id == request_id).first()
    if not req:
        return {"principal": "0.00", "disbursed": "0.00", "repaid": "0.00", "outstanding": "0.00"}
    disb = db.query(Disbursement).filter(Disbursement.request_id == request_id).all()
    rep = db.query(Repayment).filter(Repayment.request_id == request_id).all()
    disbursed = sum([Decimal(str(x.amount or 0)) for x in disb], Decimal("0"))
    repaid = sum([Decimal(str(x.amount or 0)) for x in rep], Decimal("0"))
    principal = Decimal(str(req.amount))
    outstanding = max(Decimal("0"), disbursed - repaid)
    return {
        "principal": str(principal),
        "disbursed": str(disbursed),
        "repaid": str(repaid),
        "outstanding": str(outstanding),
    }


def generate_equal_installments(total: Decimal, start: date, months: int) -> List[Dict[str, Any]]:
    if months <= 0:
        months = 1
    per = (total / months).quantize(Decimal("0.01"))
    schedule = []
    for i in range(months):
        due = (start.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
        schedule.append({"due": due.isoformat(), "amount": float(per)})
    diff = float(total) - sum([x["amount"] for x in schedule])
    if schedule:
        schedule[-1]["amount"] += round(diff, 2)
    return schedule


def set_request_status(db: Session, req: FundingRequest, status: str):
    req.status = status
    db.commit()
    db.refresh(req)
    return req
