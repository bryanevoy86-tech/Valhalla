"""PACK-PRELAUNCH-11: Arbitrage Guard Engine Service"""
from sqlalchemy.orm import Session
from . import models, schemas


def get_settings(db: Session) -> models.ArbitrageSettings:
    """Get current arbitrage settings, creating defaults if none exist."""
    s = db.query(models.ArbitrageSettings).first()
    if not s:
        s = models.ArbitrageSettings(
            mode="SAFE",
            bankroll=0.0,
            max_daily_risk=0.0,
            max_monthly_risk=0.0,
        )
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


def update_settings(db: Session, data: schemas.ArbitrageSettingsUpdate) -> models.ArbitrageSettings:
    """Update arbitrage settings."""
    settings = get_settings(db)
    
    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    db.commit()
    db.refresh(settings)
    return settings
