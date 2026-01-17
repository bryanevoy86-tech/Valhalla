from pydantic import BaseModel


class AnalyzeIn(BaseModel):
    arv: float
    repairs: float
    holding_costs: float | None = 0.0
    closing_costs: float | None = 0.0
    realtor_pct: float | None = 0.06
    assignment_fee_pct: float | None = None
    flip_discount_pct: float | None = None
    target_profit: float | None = None
    safety_buffer_pct: float | None = None
    rent_monthly: float | None = None
    taxes_annual: float | None = None
    insurance_annual: float | None = None
    maint_pct_of_rent: float | None = 0.08
    vacancy_pct_of_rent: float | None = 0.05


class StrategyOut(BaseModel):
    name: str
    mao: float
    rationale: str


class AnalyzeOut(BaseModel):
    strategies: list[StrategyOut]
    best_offer: float
    best_label: str
