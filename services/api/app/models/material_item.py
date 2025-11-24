from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.base_class import Base
import datetime

class MaterialItem(Base):
    __tablename__ = "material_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)          # "2x4 SPF", "HD Screws", "Tile - 12x24"
    category = Column(String)                      # lumber, fastener, flooring, etc.
    unit = Column(String, default="unit")          # "piece", "box", "sqft", etc.

    preferred_supplier = Column(String)            # "Home Depot", "Local Yard", etc.
    last_price = Column(Float, default=0.0)
    currency = Column(String, default="CAD")

    region = Column(String)                        # where this price applies
    notes = Column(String)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
