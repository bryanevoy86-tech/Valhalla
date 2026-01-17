from sqlalchemy import JSON, TIMESTAMP, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.sql import func

from .base import Base


class FileObject(Base):
    __tablename__ = "file_objects"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=False)
    owner_user_id = Column(Integer, index=True, nullable=True)
    kind = Column(String, nullable=True)
    key = Column(String, unique=True, index=True, nullable=False)
    filename = Column(String, nullable=False)
    mime = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default="pending")
    checksum = Column(String, nullable=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class FileAccessGrant(Base):
    __tablename__ = "file_access_grants"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(
        Integer, ForeignKey("file_objects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id = Column(Integer, index=True, nullable=True)
    role = Column(String, nullable=True)
    can_read = Column(Boolean, default=True)
    can_write = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
