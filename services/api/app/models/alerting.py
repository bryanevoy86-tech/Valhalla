from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.db.base_class import Base
import datetime


class AlertChannel(Base):
    __tablename__ = "alert_channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)               # "Bryan Email", "Phone SMS"
    channel_type = Column(String, nullable=False)       # "email", "sms", "webhook"
    target = Column(String, nullable=False)             # email address, phone, URL
    active = Column(Boolean, default=True)
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)               # "Shield Trigger", "Vault Low"
    event_type = Column(String, nullable=False)         # e.g. "SHIELD_ARMED", "VAULT_LOW"
    min_severity = Column(String, default="info")       # info/warn/critical

    channel_id = Column(Integer, nullable=False)        # FK to AlertChannel.id (logical)
    active = Column(Boolean, default=True)

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
