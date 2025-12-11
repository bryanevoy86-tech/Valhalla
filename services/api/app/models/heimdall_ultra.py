"""
PACK TC: Heimdall Ultra Mode Configuration Model
Stores operational parameters for the Ultra execution mode.
Safe, non-psychological, non-advisory behavioral settings.
"""

from sqlalchemy import Column, Integer, String, Boolean, JSON
from app.core.db import Base


class HeimdallUltraConfig(Base):
    __tablename__ = "heimdall_ultra_config"

    id = Column(Integer, primary_key=True, index=True, default=1)

    # Whether Ultra Mode is active
    enabled = Column(Boolean, default=False, nullable=False)

    # Initiative parameters
    initiative_level = Column(String, default="maximum")     # "minimal" | "normal" | "maximum"

    # Task orchestration settings
    auto_prepare_tasks = Column(Boolean, default=True)
    auto_generate_next_steps = Column(Boolean, default=True)
    auto_close_loops = Column(Boolean, default=True)

    # Escalation framework
    escalation_chain = Column(JSON, default=lambda: {
        "operations": "ODIN",
        "risk": "TYR",
        "creativity": "LOKI",
        "family": "QUEEN",
        "default": "KING"
    })

    # Governance hierarchy priorities
    priority_matrix = Column(JSON, default=lambda: [
        "family_stability",
        "financial_safety",
        "empire_growth",
        "operational_velocity",
        "energy_conservation",
        "mental_load_reduction"
    ])

    # System scanning rules
    scan_enabled = Column(Boolean, default=True)
    scan_frequency_minutes = Column(Integer, default=60)

    # Zero-drop memory pipeline
    track_all_user_inputs = Column(Boolean, default=True)

    # Tempo ruleset reference
    tempo_profile = Column(String, default="default")

    def __repr__(self):
        return f"<HeimdallUltraConfig(enabled={self.enabled}, initiative={self.initiative_level})>"
