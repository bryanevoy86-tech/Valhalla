"""PACK 94: Zone Replication - Schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ZoneReplicationBase(BaseModel):
    source_zone_id: int
    target_zone_id: int
    included_modules: str
    status: str = "pending"


class ZoneReplicationCreate(ZoneReplicationBase):
    pass


class ZoneReplicationOut(ZoneReplicationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
