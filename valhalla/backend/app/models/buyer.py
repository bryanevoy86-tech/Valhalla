from sqlalchemy import Boolean, Column, Float, Integer, String

from ..core.db import Base


class Buyer(Base):
    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    phone = Column(String, default="")
    legacy_id = Column(String, default="primary", index=True)

    # buy box
    markets = Column(String, default="")  # comma CSV like "winnipeg,brandon,toronto"
    zips = Column(String, default="")  # comma CSV for postal/zip codes
    price_min = Column(Float, default=0.0)
    price_max = Column(Float, default=9e12)
    beds_min = Column(Float, default=0.0)
    baths_min = Column(Float, default=0.0)
    property_types = Column(String, default="")  # CSV: "sfh,duplex,triplex,mfh,land"
    tags = Column(String, default="")  # CSV: "cash,hard-money,quick-close"
    active = Column(Boolean, default=True)
