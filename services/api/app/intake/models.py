"""Deal intake models - real-world entry point."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Deal(Base):
    """
    Deal model - intake from external sources (websites, MLSs, partners, etc).
    
    Represents raw deal data coming into the system.
    """
    __tablename__ = "deals"
    
    id = Column(String, primary_key=True)
    source = Column(String)  # e.g., "zillow", "mls", "partner_api", "manual"
    payload = Column(JSON)  # Raw data from source
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Deal {self.id} from {self.source}>"
