"""Deal intake models - real-world entry point."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class DealIntakeRecord(Base):
    """
    Deal intake record - external deal sources (websites, MLSs, partners, etc).
    
    Represents raw deal data coming into the system. Does NOT map to production deals table.
    This is a separate tracking entity for raw incoming deals before pipeline processing.
    """
    __tablename__ = "deal_intake_records"
    
    id = Column(String, primary_key=True)
    source = Column(String)  # e.g., "zillow", "mls", "partner_api", "manual"
    payload = Column(JSON)  # Raw data from source
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<DealIntakeRecord {self.id} from {self.source}>"


# Backward compatibility alias - deprecated, use DealIntakeRecord instead
Deal = DealIntakeRecord
