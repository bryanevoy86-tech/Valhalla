"""
PACK AI: Scenario Simulator Schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ScenarioCreate(BaseModel):
    key: str = Field(..., description="Unique scenario key, e.g. 'brrrr_scale_v1'")
    name: str
    description: Optional[str] = None
    created_by: Optional[str] = None


class ScenarioOut(BaseModel):
    id: int
    key: str
    name: str
    description: Optional[str]
    created_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ScenarioRunCreate(BaseModel):
    scenario_id: int
    input_payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary input parameters for the scenario run",
    )


class ScenarioRunUpdate(BaseModel):
    status: Optional[str] = None
    result_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ScenarioRunOut(BaseModel):
    id: int
    scenario_id: int
    input_payload: Dict[str, Any]
    result_payload: Optional[Dict[str, Any]]
    status: str
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
