from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.db import Base


class LegacyInstance(Base):
    __tablename__ = "legacy_instances"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)  # e.g., "LEG-0007"
    region = Column(String, nullable=False)  # e.g., "CA", "PA", "BS"
    api_base = Column(String, nullable=False)  # https://valhalla-*.onrender.com
    status = Column(String, default="ready")  # ready|cloning|active|paused|error
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ClonePlan(Base):
    __tablename__ = "clone_plans"
    id = Column(Integer, primary_key=True, index=True)
    source_instance_id = Column(Integer, ForeignKey("legacy_instances.id"))
    target_region = Column(String, nullable=False)
    modules = Column(JSON, nullable=False)  # e.g., {"wholesaling": true, "brrrr": false}
    safe_mode = Column(Boolean, default=True)
    status = Column(String, default="queued")  # queued|running|completed|failed
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    source = relationship("LegacyInstance", backref="clone_plans")


class MirrorLink(Base):
    __tablename__ = "mirror_links"
    id = Column(Integer, primary_key=True, index=True)
    primary_instance_id = Column(Integer, ForeignKey("legacy_instances.id"))
    secondary_instance_id = Column(Integer, ForeignKey("legacy_instances.id"))
    mode = Column(String, default="hot")  # hot|warm|cold
    traffic_split = Column(Integer, default=50)  # % to secondary for hot mode
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
