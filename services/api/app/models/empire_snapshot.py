from sqlalchemy import Column, Integer, String, DateTime, Text
import datetime
from app.db.base_class import Base


class EmpireSnapshot(Base):
    __tablename__ = "empire_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, nullable=False)
    snapshot_type = Column(String, default="manual")
    summary_json = Column(Text, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

__all__ = ["EmpireSnapshot"]
