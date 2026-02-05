from __future__ import annotations
from datetime import date
from pydantic import BaseModel, Field

class EngineUpsertIn(BaseModel):
    code: str
    name: str
    category: str
    description: str | None = None
    status: str = "DESIGNED"
    requires_approval: bool = True
    sandbox_only: bool = True

class RevenueEventIn(BaseModel):
    engine_code: str
    gross_amount: float
    currency: str = "USD"
    source_ref: str | None = None
    as_of_date: date

class RevenueEventOut(BaseModel):
    engine_code: str
    gross_amount: float
    fun_fund_amount: float
    reinvest_amount: float
    ops_reserve_amount: float
    currency: str
    as_of_date: date

class TargetUpsertIn(BaseModel):
    engine_code: str = "SYSTEM"
    month: date
    currency: str = "USD"
    min_gross: float = 0
    min_fun_fund: float = 0

class TrajectoryStatusOut(BaseModel):
    month: date
    currency: str
    actual_gross: float
    target_gross: float
    gross_delta: float
    actual_fun_fund: float
    target_fun_fund: float
    fun_fund_delta: float
    ok: bool
    severity: str  # OK/WARNING/CRITICAL
