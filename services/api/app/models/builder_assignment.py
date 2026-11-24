"""Owner-approved handoffs to the isolated Builder test process."""
from sqlalchemy import Column, DateTime, Integer, JSON, String, Uuid

from app.core.db import Base


class BuilderAssignment(Base):
    __tablename__ = "prime_builder_assignments"
    id = Column(Uuid(), primary_key=True)
    task_id = Column(Integer(), nullable=False)
    base_commit = Column(String(40), nullable=False)
    bundle_sha256 = Column(String(64), nullable=False)
    image_id = Column(String(71), nullable=False)
    status = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime(), nullable=False)
    claim_count = Column(Integer(), nullable=False, default=0, server_default="0")
    lease_id = Column(Uuid())
    lease_until = Column(DateTime())
    receipt = Column(JSON())
