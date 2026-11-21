from pydantic import BaseModel, Field
from typing import Literal
from typing import Optional


class FXRuleCreate(BaseModel):
    name: str
    param: str
    value: float
    active: bool = True


class FXRuleResponse(FXRuleCreate):
    id: int

    class Config:
        from_attributes = True


class FXOrderCreate(BaseModel):
    pair: str
    side: Literal["buy", "sell"]
    size: float = Field(gt=0, le=1_000_000, allow_inf_nan=False)
    entry_px: float = Field(gt=0, le=100_000, allow_inf_nan=False)
    meta: Optional[dict] = None


class FXOrderResponse(FXOrderCreate):
    basis: Literal["LEGACY_PAPER_BOOK"] = "LEGACY_PAPER_BOOK"
    id: int
    status: str
    exit_px: Optional[float] = None

    class Config:
        from_attributes = True


class FXCloseRequest(BaseModel):
    exit_px: float = Field(gt=0, le=100_000, allow_inf_nan=False)


class FXMetricResponse(BaseModel):
    basis: Literal["LEGACY_PAPER_BOOK"] = "LEGACY_PAPER_BOOK"
    id: int
    equity: float
    peak_equity: float
    drawdown_pct: float
    note: Optional[str]

    class Config:
        from_attributes = True
