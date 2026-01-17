# app/heimdall/optimization_control.py
from pydantic import BaseModel
from enum import Enum

class GovernanceMode(str, Enum):
    HUMAN_FINAL_SAY = "human_final_say"
    HYBRID = "hybrid"
    FULL_AUTONOMY = "full_autonomy"

class EvolutionMode(str, Enum):
    CONSERVATIVE = "conservative"
    ASCENDED_OPTIMIZER = "ascended_optimizer"
    ETERNAL_OPTIMIZATION = "eternal_optimization"

class ShieldStatus(str, Enum):
    OFF = "off"
    CAUTION = "caution"
    FULL_SHIELD = "full_shield"

class OptimizationSettings(BaseModel):
    governance_mode: GovernanceMode = GovernanceMode.HYBRID
    evolution_mode: EvolutionMode = EvolutionMode.ASCENDED_OPTIMIZER
    shield_status: ShieldStatus = ShieldStatus.CAUTION
    auto_clone_enabled: bool = False
    notes: str | None = None

# Simple in-memory store for now – Heimdall will later persist to DB
_current_settings = OptimizationSettings()

class OptimizationControlService:
    @staticmethod
    async def get_settings() -> OptimizationSettings:
        return _current_settings

    @staticmethod
    async def update_settings(payload: OptimizationSettings) -> OptimizationSettings:
        global _current_settings
        _current_settings = payload
        return _current_settings
