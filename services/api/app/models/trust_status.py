from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.db.base_class import Base
import datetime


class TrustStatus(Base):
    __tablename__ = "trust_status"

    id = Column(Integer, primary_key=True, index=True)
    trust_code = Column(String, nullable=False)      # "PANAMA_MASTER", "CAN_FAMILY_1", etc.
    display_name = Column(String, nullable=False)    # human name

    # core milestones
    lawyer_engaged = Column(Boolean, default=False)
    draft_complete = Column(Boolean, default=False)
    signed = Column(Boolean, default=False)
    bank_accounts_open = Column(Boolean, default=False)
    life_policies_assigned = Column(Boolean, default=False)
    property_titled = Column(Boolean, default=False)

    # overall state
    status = Column(String, default="pending")       # pending / in-progress / active / archived
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
