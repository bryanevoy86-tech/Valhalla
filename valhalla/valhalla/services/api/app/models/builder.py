from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from ..core.db import Base


class BuilderTask(Base):
    __tablename__ = "builder_tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(140), nullable=False)
    scope = Column(String(200), nullable=False)
    status = Column(String(32), nullable=False, server_default="queued")
    plan = Column(Text, nullable=True)
    diff_summary = Column(Text, nullable=True)
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class BuilderEvent(Base):
    __tablename__ = "builder_events"

    id = Column(Integer, primary_key=True)
    kind = Column(String(40), nullable=False)
    msg = Column(Text, nullable=True)
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
