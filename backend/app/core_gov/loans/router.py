from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core_gov.audit.audit_log import audit
from app.core_gov.loans.models import LoanIn, Loan
from app.core_gov.loans.store import add_loan, get_loan, list_loans, load_loans
from app.core_gov.loans.underwriting import build_underwriting_checklist
from app.core_gov.loans.recommend import recommend_next_step
from app.core_gov.loans.priority import rank

router = APIRouter(prefix="/loans", tags=["Core: Loans"])


@router.post("", response_model=Loan)
def create(payload: LoanIn):
    l = add_loan(payload.model_dump())
    audit("LOAN_CREATED", {"id": l["id"], "name": l["name"], "country": l.get("country")})
    return l


@router.get("")
def list_(q: str | None = None, country: str | None = None, province_state: str | None = None, product_type: str | None = None, limit: int = 50):
    return {"items": list_loans(q=q, country=country, province_state=province_state, product_type=product_type, limit=limit)}


@router.get("/{loan_id}")
def get_(loan_id: str):
    l = get_loan(loan_id)
    if not l:
        raise HTTPException(status_code=404, detail="Loan not found")
    return l


@router.post("/{loan_id}/underwriting_checklist")
def underwriting(loan_id: str):
    l = get_loan(loan_id)
    if not l:
        raise HTTPException(status_code=404, detail="Loan not found")
    return build_underwriting_checklist(l)


class LoanProfile(BaseModel):
    country: str = "CA"
    province_state: str | None = None
    has_credit_history: bool = False
    has_revenue_history: bool = False
    needs_amount: float | None = None


@router.post("/recommend_next")
def recommend(payload: LoanProfile):
    res = recommend_next_step(payload.model_dump(), load_loans())
    audit("LOAN_NEXT_RECOMMENDATION", {"country": payload.country, "province_state": payload.province_state})
    return res


@router.get("/rank")
def rank_loans(limit: int = 25):
    return rank(limit=limit)

