from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric, UniqueConstraint
from app.models.base import Base

class EngineActivationRule(Base):
    """
    Heimdall uses these rules to determine if an engine can move from PAPER/TESTING to LIVE.
    """
    __tablename__ = "engine_activation_rules"
    __table_args__ = (UniqueConstraint("engine_code", name="uq_engine_activation_rules_engine_code"),)

    id = Column(Integer, primary_key=True, index=True)

    engine_code = Column(String, nullable=False)

    # Minimum performance gates (tune later)
    min_monthly_gross = Column(Numeric(18, 2), nullable=False, default=0)
    min_success_rate = Column(Numeric(6, 3), nullable=False, default=0)   # 0.000–1.000
    max_risk_score = Column(Numeric(6, 3), nullable=False, default=1)     # 0.000–1.000

    # Mandatory gates
    require_contracts_ready = Column(Boolean, nullable=False, default=False)
    require_compliance_ready = Column(Boolean, nullable=False, default=False)
    require_payment_rails_ready = Column(Boolean, nullable=False, default=False)

    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
