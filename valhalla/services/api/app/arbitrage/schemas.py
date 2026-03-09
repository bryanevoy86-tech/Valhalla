from pydantic import BaseModel
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
    side: str  # buy|sell
    size: float
    entry_px: float
    meta: Optional[dict] = None


class FXOrderResponse(FXOrderCreate):
    id: int
    status: str
    exit_px: Optional[float] = None

    class Config:
        from_attributes = True


class FXCloseRequest(BaseModel):
    exit_px: float


class FXMetricResponse(BaseModel):
    id: int
    equity: float
    peak_equity: float
    drawdown_pct: float
    note: Optional[str]

    class Config:
        from_attributes = True
