"""
Pack 57: Pantry Photo Inventory - Models
"""
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, Boolean, Float, ForeignKey, DateTime
from datetime import datetime
from app.core.db import Base

class PantryLocation(Base):
    __tablename__ = "pantry_locations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

class PantryItem(Base):
    __tablename__ = "pantry_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    tags: Mapped[str | None] = mapped_column(String(256))
    unit: Mapped[str] = mapped_column(String(16), default="ea")
    reorder_at: Mapped[float] = mapped_column(Float, default=1.0)
    target_qty: Mapped[float] = mapped_column(Float, default=2.0)
    auto_reorder: Mapped[bool] = mapped_column(Boolean, default=True)

class PantryStock(Base):
    __tablename__ = "pantry_stocks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("pantry_items.id", ondelete="CASCADE"))
    location_id: Mapped[int] = mapped_column(Integer, ForeignKey("pantry_locations.id", ondelete="CASCADE"))
    qty: Mapped[float] = mapped_column(Float, default=0.0)

class PantryPhoto(Base):
    __tablename__ = "pantry_photos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("pantry_items.id", ondelete="SET NULL"))
    file_name: Mapped[str] = mapped_column(String(256), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(256))
    detected_tags: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PantryTxn(Base):
    __tablename__ = "pantry_txns"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("pantry_items.id", ondelete="CASCADE"))
    location_id: Mapped[int] = mapped_column(Integer, ForeignKey("pantry_locations.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16))  # in|out|move
    qty: Mapped[float] = mapped_column(Float)
    note: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PantryReorder(Base):
    __tablename__ = "pantry_reorders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("pantry_items.id", ondelete="CASCADE"))
    suggested_qty: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16), default="suggested")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
