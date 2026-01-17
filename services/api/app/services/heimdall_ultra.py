"""
PACK TC: Heimdall Ultra Mode Logic Layer
Defines service functions for managing Ultra Mode configuration.
"""

from sqlalchemy.orm import Session
from datetime import datetime
from app.models.heimdall_ultra import HeimdallUltraConfig
from app.schemas.heimdall_ultra import UltraConfigUpdate


def get_ultra_config(db: Session) -> HeimdallUltraConfig:
    """Retrieve Ultra Mode config (singleton pattern, always ID=1)."""
    cfg = db.query(HeimdallUltraConfig).filter(HeimdallUltraConfig.id == 1).first()
    if not cfg:
        cfg = HeimdallUltraConfig(id=1)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def update_ultra_config(db: Session, payload: UltraConfigUpdate) -> HeimdallUltraConfig:
    """Update Ultra Mode configuration with partial update support."""
    cfg = get_ultra_config(db)

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cfg, key, value)

    db.commit()
    db.refresh(cfg)
    return cfg


def toggle_ultra_mode(db: Session, enabled: bool = True) -> HeimdallUltraConfig:
    """Enable or disable Ultra Mode."""
    cfg = get_ultra_config(db)
    cfg.enabled = enabled
    db.commit()
    db.refresh(cfg)
    return cfg


def set_initiative_level(db: Session, level: str) -> HeimdallUltraConfig:
    """Set the initiative level: 'minimal', 'normal', or 'maximum'."""
    if level not in ["minimal", "normal", "maximum"]:
        raise ValueError(f"Invalid initiative level: {level}")
    cfg = get_ultra_config(db)
    cfg.initiative_level = level
    db.commit()
    db.refresh(cfg)
    return cfg


def set_escalation_chain(db: Session, chain: dict) -> HeimdallUltraConfig:
    """Update the escalation routing chain."""
    cfg = get_ultra_config(db)
    cfg.escalation_chain = chain
    db.commit()
    db.refresh(cfg)
    return cfg


def set_priority_matrix(db: Session, priorities: list) -> HeimdallUltraConfig:
    """Update the priority decision matrix."""
    cfg = get_ultra_config(db)
    cfg.priority_matrix = priorities
    db.commit()
    db.refresh(cfg)
    return cfg
