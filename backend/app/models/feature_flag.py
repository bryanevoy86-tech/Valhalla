from sqlalchemy import JSON, TIMESTAMP, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.sql import func

from ..core.db import Base


class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String, nullable=False, default="global")
    key = Column(String, nullable=False, index=True)
    enabled = Column(Boolean, nullable=False, default=True)
    payload = Column(JSON, nullable=True)
    org_id = Column(Integer, ForeignKey("orgs.id", ondelete="CASCADE"), index=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class AdminAction(Base):
    __tablename__ = "admin_actions"
    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    org_id = Column(Integer, ForeignKey("orgs.id", ondelete="SET NULL"), index=True, nullable=True)
    action = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
