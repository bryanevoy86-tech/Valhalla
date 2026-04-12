"""
ExecutionPolicy model - stores conservative policies for assessment
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func
from app.core.db import Base


class ExecutionPolicy(Base):
    """
    Execution policy - rules, buffers, thresholds for processing opportunities.
    Used by assessment and routing services.
    """
    __tablename__ = "execution_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Policy scope
    domain = Column(String(50), nullable=False, index=True)  # cost_buffers, confidence_rules, risk_rules, strategy_mapping
    policy_type = Column(String(50), nullable=False)         # percentage, absolute, threshold, enum_mapping
    rule_key = Column(String(200), nullable=False, unique=True, index=True)
    
    # Rule definition (JSON)
    rule_value_json = Column(Text, nullable=False)
    
    # Metadata
    description = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ExecutionPolicy {self.rule_key} | active={self.active}>"
