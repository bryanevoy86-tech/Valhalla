from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
import datetime
from app.core.db import Base


class GlobalSetting(Base):
    __tablename__ = "global_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False, unique=True)
    value = Column(String, nullable=False)
    category = Column(String, default="core")
    description = Column(Text)
    is_feature_flag = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


__all__ = ["GlobalSetting"]
