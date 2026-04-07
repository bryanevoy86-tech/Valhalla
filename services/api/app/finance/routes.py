from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.finance.deal_ledger import DealLedger
from app.finance.disbursement_engine import build_disbursement_plan
from app.finance.finance_control_service import (
    queue_financial_intent_for_approval,
    get_financial_intent_status,
    approve_financial_intent,
    set_finance_freeze,
)
from app.finance.status_feed import (
    get_finance_status_summary,
    get_finance_status_feed,
    get_finance_audit_feed,
)
from app.finance.financial_package_builder import build_financial_package
from app.finance.package_approval_orchestrator import approve_financial_package
from app.finance.package_status_feed import get_financial_package_history


router = APIRouter(prefix="/api/finance", tags=["Finance"])


class CreateLedgerRequest(BaseModel):
    deal_id: str
    purchase_price: float = 0.0
    assignment_fee: float = 0.0
    earnest_money: float = 0.0
    closing_costs: float = 0.0


class DisbursementRequest(BaseModel):
    deal_id: str
    purchase_price: float = 0.0
    assignment_fee: float = 0.0
    earnest_money: float = 0.0
    closing_costs: float = 0.0


class FinanceIntentRequest(BaseModel):
    deal_id: str
    intent_id: str
    amount: float
    purpose: str
    payee: str
    requested_by: str


class FinanceApproveRequest(BaseModel):
    approver: str


class FinanceFreezeRequest(BaseModel):
    frozen: bool
    reason: str | None = None


class FinancialPackageApproveRequest(BaseModel):
    deal_id: str
    deal_data: dict
    approver: str


@router.post("/ledger/create")
def create_ledger(data: CreateLedgerRequest):
    ledger = DealLedger(
        deal_id=data.deal_id,
        purchase_price=data.purchase_price,
        assignment_fee=data.assignment_fee,
        earnest_money=data.earnest_money,
        closing_costs=data.closing_costs,
    )
    ledger.calculate_expected_profit()
    return ledger.to_dict()


@router.post("/disbursement/plan")
def generate_disbursement(data: DisbursementRequest):
    plan = build_disbursement_plan(data.deal_id, data.dict())
    return {"intents": [p.to_dict() for p in plan]}


@router.post("/intent/queue")
def queue_finance_intent(req: FinanceIntentRequest):
    return queue_financial_intent_for_approval(
        deal_id=req.deal_id,
        intent_id=req.intent_id,
        amount=req.amount,
        purpose=req.purpose,
        payee=req.payee,
        requested_by=req.requested_by,
    )


@router.get("/intent/{intent_id}")
def get_finance_intent(intent_id: str):
    try:
        return get_financial_intent_status(intent_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/intent/{intent_id}/approve")
def approve_finance_intent(intent_id: str, req: FinanceApproveRequest):
    try:
        return approve_financial_intent(intent_id, req.approver)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/freeze")
def finance_freeze(req: FinanceFreezeRequest):
    return set_finance_freeze(req.frozen, req.reason)


@router.get("/status/summary")
def finance_status_summary():
    return get_finance_status_summary()


@router.get("/status/feed")
def finance_status_feed(limit: int = 100):
    return get_finance_status_feed(limit=limit)


@router.get("/status/audit")
def finance_audit_feed(limit: int = 200):
    return get_finance_audit_feed(limit=limit)


@router.post("/package/build")
def build_finance_package(data: dict):
    return build_financial_package(data).__dict__


@router.post("/package/approve")
def approve_finance_package(req: FinancialPackageApproveRequest):
    return approve_financial_package(
        deal_id=req.deal_id,
        deal_data=req.deal_data,
        approver=req.approver,
    )


@router.get("/status/packages")
def finance_package_history(limit: int = 100):
    return get_financial_package_history(limit=limit)
