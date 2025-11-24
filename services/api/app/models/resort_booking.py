from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.base_class import Base
import datetime

class ResortBooking(Base):
    __tablename__ = "resort_bookings"

    id = Column(Integer, primary_key=True, index=True)
    guest_name = Column(String, nullable=False)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    room_type = Column(String)
    base_price = Column(Float)
    dynamic_price = Column(Float)
    status = Column(String, default="reserved")  # reserved / checked-in / completed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
