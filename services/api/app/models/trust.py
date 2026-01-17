from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from app.db.base_class import Base
import datetime

class Trust(Base):
    __tablename__ = "trusts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # e.g. "Panama Master Trust"
    jurisdiction = Column(String, nullable=False)  # Panama, Canada, Bahamas, NZ, etc.
    status = Column(String, default="active")  # active / pending / archived

    routing_priority = Column(Integer, default=1)  # determines income/filter order
    tax_exempt = Column(Boolean, default=False)
    vault_balance = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
