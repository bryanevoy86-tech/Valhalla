from sqlalchemy import Boolean, Column, Integer, String

from ..core.db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, default="")
    role = Column(String, default="viewer")
    legacies = Column(String, default="[]")  # JSON string of legacy IDs
    is_active = Column(Boolean, default=True)
