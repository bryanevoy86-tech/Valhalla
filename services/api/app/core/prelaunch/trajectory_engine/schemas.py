"""Trajectory Engine Schemas"""
from typing import Optional, List
from pydantic import BaseModel


class TrajectoryPoint(BaseModel):
    month: int
    cashflow: float
    net_worth: float
    risk_level: str


class CurrentTrajectory(BaseModel):
    months: List[TrajectoryPoint]


class ScenarioRequest(BaseModel):
    additional_deals: int = 0
    bankroll_change: float = 0
    expense_change: float = 0
    months_ahead: int = 12


class ScenarioResult(CurrentTrajectory):
    confidence: float
    notes: List[str]
