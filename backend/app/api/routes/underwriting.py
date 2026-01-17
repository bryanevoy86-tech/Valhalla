from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...schemas.deal import DealCreate, DealOut
from ...schemas.underwrite import AnalyzeIn, AnalyzeOut
from ...services.underwriting import AnalyzeInput, analyze, compute_mao
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/underwriting", tags=["underwriting"])


@router.post("/analyze", response_model=AnalyzeOut)
def analyze_deal(payload: AnalyzeIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _ = db
    _ = user
    res = analyze(AnalyzeInput(**payload.model_dump()))
    return AnalyzeOut(
        strategies=[
            {"name": s.name, "mao": s.mao, "rationale": s.rationale} for s in res.strategies
        ],
        best_offer=res.best_offer,
        best_label=res.best_label,
    )


@router.post("/mao", response_model=DealOut)
def calc_mao(
    data: DealCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _ = db
    _ = user
    mao = compute_mao(arv=data.arv, repairs=data.repairs, fee=0.08)
    return DealOut(id=0, **{**data.model_dump(), "mao": mao})
