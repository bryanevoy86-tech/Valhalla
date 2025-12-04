from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
import datetime
from app.db.base_class import Base


class RentalProperty(Base):
    __tablename__ = "rental_properties"

    id = Column(Integer, primary_key=True, index=True)
    legacy_code = Column(String, nullable=False)
    zone_code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    address_line1 = Column(String, nullable=False)
    address_line2 = Column(String)
    city = Column(String)
    region = Column(String)
    country = Column(String, nullable=False)
    postal_code = Column(String)
    property_type = Column(String, default="single")
    bedrooms = Column(Integer, default=0)
    bathrooms = Column(Float, default=0.0)
    square_feet = Column(Integer, default=0)
    purchase_price = Column(Float, default=0.0)
    arv = Column(Float, default=0.0)
    current_value = Column(Float, default=0.0)
    status = Column(String, default="acquisition")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
