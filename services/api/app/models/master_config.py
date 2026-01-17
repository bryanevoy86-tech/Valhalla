from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from app.db.base_class import Base
import datetime


class MasterConfig(Base):
    __tablename__ = "master_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String, nullable=False, unique=True)
    value_type = Column(String, nullable=False, default="string")
    value_string = Column(Text)
    value_float = Column(Float)
    value_int = Column(Integer)
    value_bool = Column(Boolean)
    value_json = Column(Text)
    description = Column(Text)
    ai_mutable = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
