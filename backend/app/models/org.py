from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from ..core.db import Base


class Org(Base):
    __tablename__ = "orgs"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    members = relationship("OrgMember", back_populates="org", cascade="all, delete")


class OrgMember(Base):
    __tablename__ = "org_members"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role = Column(String, nullable=False, default="member")
    __table_args__ = (UniqueConstraint("org_id", "user_id", name="uq_org_user"),)
    org = relationship("Org", back_populates="members")
    user = relationship("User", backref="org_memberships")
