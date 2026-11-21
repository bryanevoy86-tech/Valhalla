"""Synthetic provider probe results linked to one metered attempt."""
from sqlalchemy import Column, Integer, String, Uuid

from app.core.db import Base


class SpecialistProbe(Base):
    __tablename__ = "prime_specialist_probes"
    id = Column(Uuid(), primary_key=True)
    role = Column(String(40), nullable=False)
    provider_id = Column(Integer(), nullable=False)
    model = Column(String(160), nullable=False)
    case_id = Column(String(80), nullable=False)
    result = Column(String(20), nullable=False)
