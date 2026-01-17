from sqlalchemy import JSON, TIMESTAMP, Boolean, Column, Integer, String
from sqlalchemy.sql import func

from ..core.db import Base


class IpRule(Base):
    __tablename__ = "ip_rules"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=True)
    label = Column(String, nullable=True)
    cidr = Column(String, nullable=False)
    action = Column(String, nullable=False, default="allow")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=True)
    user_id = Column(Integer, index=True, nullable=True)
    name = Column(String, nullable=False)
    prefix = Column(String, nullable=False, index=True)
    hash = Column(String, nullable=False)
    scopes = Column(JSON, nullable=True)
    active = Column(Boolean, default=True, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class RateLimit(Base):
    __tablename__ = "rate_limits"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False, index=True)
    window_sec = Column(Integer, nullable=False)
    max_hits = Column(Integer, nullable=False)
    active = Column(Boolean, default=True, index=True)
    note = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class RequestLog(Base):
    __tablename__ = "request_logs"
    id = Column(Integer, primary_key=True, index=True)
    ts = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    ip = Column(String, index=True)
    user_id = Column(Integer, index=True, nullable=True)
    org_id = Column(Integer, index=True, nullable=True)
    route = Column(String, index=True)
    method = Column(String)
    status = Column(Integer)
    meta = Column(JSON)
