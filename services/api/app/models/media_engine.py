"""
PACK AC: Content / Media Engine Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class MediaChannel(Base):
    __tablename__ = "media_channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)          # e.g. YouTube, TikTok, Blog, Email
    slug = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    publishes = relationship(
        "MediaPublishLog",
        back_populates="channel",
        cascade="all, delete-orphan",
    )


class MediaContent(Base):
    __tablename__ = "media_contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content_type = Column(String, nullable=False)   # script, article, post, video_script, etc.
    body = Column(Text, nullable=False)

    tags = Column(String, nullable=True)           # comma-separated tags
    audience = Column(String, nullable=True)       # public, internal, kids, investors, etc.

    created_at = Column(DateTime, default=datetime.utcnow)


class MediaPublishLog(Base):
    __tablename__ = "media_publish_logs"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("media_contents.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("media_channels.id"), nullable=False)

    status = Column(String, nullable=False, default="planned")  # planned, published, cancelled
    external_ref = Column(String, nullable=True)                # URL, video_id, etc.

    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    channel = relationship("MediaChannel", back_populates="publishes")
