"""PACK-PRELAUNCH-11: Arbitrage Guard Engine Schemas"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ArbitrageSettingsBase(BaseModel):
    mode: str
    bankroll: float
    max_daily_risk: float
    max_monthly_risk: float


class ArbitrageSettingsRead(ArbitrageSettingsBase):
    id: UUID
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArbitrageSettingsUpdate(BaseModel):
    mode: str | None = None
    bankroll: float | None = None
    max_daily_risk: float | None = None
    max_monthly_risk: float | None = None
