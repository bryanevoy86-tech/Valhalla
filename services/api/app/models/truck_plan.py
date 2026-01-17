from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.db.base_class import Base
import datetime


class TruckPlan(Base):
    __tablename__ = "truck_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="Valhalla Truck")

    target_price = Column(Float, nullable=False)            # total estimated cost (truck + taxes)
    wrap_budget = Column(Float, default=0.0)
    extras_budget = Column(Float, default=0.0)              # bumpers, bars, lights, etc.

    business_credit_target = Column(Float, default=0.0)     # e.g. credit line goal
    current_business_credit = Column(Float, default=0.0)

    funfund_contribution_target = Column(Float, default=0.0)  # how much Fun Fund to put towards it
    funfund_contributed = Column(Float, default=0.0)

    status = Column(String, default="planning")             # planning / saving / ready / purchased
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
