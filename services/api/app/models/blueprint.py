"""PACK 68: Blueprint Generator Core
Produces structural layouts, floorplans, and schematic data objects.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text

from app.models.base import Base


class Blueprint(Base):
    __tablename__ = "blueprint"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, nullable=False)
    property_address = Column(String, nullable=True)
    specs_payload = Column(Text, nullable=False)
    status = Column(String, default="generated")
    created_at = Column(DateTime, default=datetime.utcnow)
