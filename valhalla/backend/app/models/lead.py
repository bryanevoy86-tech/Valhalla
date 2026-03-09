from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..core.db import Base


class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    org_id = Column(Integer, ForeignKey("orgs.id", ondelete="CASCADE"), index=True, nullable=True)
    name = Column(String, nullable=False)
    phone = Column(String, default="")
    email = Column(String, default="")
    address = Column(Text, default="")
    status = Column(String, default="new")
    tags = Column(String, default="")  # comma-separated
    notes = Column(Text, default="")
    legacy_id = Column(String, default="primary", index=True)  # multi-legacy support
    owner = relationship("User")
