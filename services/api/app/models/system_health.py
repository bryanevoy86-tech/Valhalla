from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.db.base_class import Base
import datetime


class SystemHealthSnapshot(Base):
    __tablename__ = "system_health_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    scope = Column(String, nullable=False)
    scope_code = Column(String)

    health_score = Column(Float, default=1.0)

    income_status = Column(String, default="green")
    liquidity_status = Column(String, default="green")
    deal_flow_status = Column(String, default="green")
    compliance_status = Column(String, default="green")
    ai_status = Column(String, default="green")

    summary = Column(Text)
    details_json = Column(Text)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


__all__ = ["SystemHealthSnapshot"]
