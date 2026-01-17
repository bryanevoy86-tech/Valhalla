from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.core.db import Base


class Closer(Base):
    __tablename__ = "closers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    success_rate = Column(Float, default=0.0)  # Percentage of successful deals
    last_interaction = Column(DateTime, nullable=True)  # Last negotiation date
    current_target = Column(String, nullable=True)  # Current deal type or negotiation target

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Closer(name={self.name}, success_rate={self.success_rate})>"
