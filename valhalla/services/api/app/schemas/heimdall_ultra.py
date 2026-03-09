"""
PACK TC: Heimdall Ultra Mode Schemas
Defines request/response models for Ultra Mode configuration.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class UltraConfigBase(BaseModel):
    enabled: bool = Field(..., description="Whether Ultra Mode is active.")
    initiative_level: str = Field(..., description="Execution intensity level: 'minimal', 'normal', or 'maximum'.")
    auto_prepare_tasks: bool = Field(default=True, description="Automatically prepare next tasks.")
    auto_generate_next_steps: bool = Field(default=True, description="Auto-generate execution steps.")
    auto_close_loops: bool = Field(default=True, description="Automatically close task loops.")
    escalation_chain: Dict[str, str] = Field(default_factory=lambda: {
        "operations": "ODIN",
        "risk": "TYR",
        "creativity": "LOKI",
        "family": "QUEEN",
        "default": "KING"
    }, description="Escalation routing by category.")
    priority_matrix: List[str] = Field(default_factory=lambda: [
        "family_stability",
        "financial_safety",
        "empire_growth",
        "operational_velocity",
        "energy_conservation",
        "mental_load_reduction"
    ], description="Priority ordering for decision-making.")
    scan_enabled: bool = Field(default=True, description="Enable system scanning.")
    scan_frequency_minutes: int = Field(default=60, description="Scan frequency in minutes.")
    track_all_user_inputs: bool = Field(default=True, description="Track all user inputs for memory pipeline.")
    tempo_profile: str = Field(default="default", description="Reference to daily tempo ruleset.")


class UltraConfigOut(UltraConfigBase):
    id: int = Field(..., description="Config ID (always 1).")

    class Config:
        from_attributes = True


class UltraConfigUpdate(BaseModel):
    enabled: Optional[bool] = Field(None, description="Whether Ultra Mode is active.")
    initiative_level: Optional[str] = Field(None, description="Execution intensity level.")
    auto_prepare_tasks: Optional[bool] = Field(None, description="Automatically prepare tasks.")
    auto_generate_next_steps: Optional[bool] = Field(None, description="Auto-generate execution steps.")
    auto_close_loops: Optional[bool] = Field(None, description="Automatically close loops.")
    escalation_chain: Optional[Dict[str, str]] = Field(None, description="Escalation routing.")
    priority_matrix: Optional[List[str]] = Field(None, description="Priority ordering.")
    scan_enabled: Optional[bool] = Field(None, description="Enable system scanning.")
    scan_frequency_minutes: Optional[int] = Field(None, description="Scan frequency in minutes.")
    track_all_user_inputs: Optional[bool] = Field(None, description="Track all inputs.")
    tempo_profile: Optional[str] = Field(None, description="Tempo ruleset reference.")
