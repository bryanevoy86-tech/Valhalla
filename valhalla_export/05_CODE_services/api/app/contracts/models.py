"""Contract pipeline data models.

NOTE: This module has been consolidated with app.models.contracts.
The primary Contract and ContractEvent models are now defined there.
This file is kept for backwards compatibility and re-exports the canonical models.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Text, DateTime
from sqlalchemy.sql import func
from app.core.db import Base

# Re-export the canonical models from app.models.contracts
from app.models.contracts import Contract, ContractEvent, ContractTemplate, ContractParty, ContractDocument, ContractEnvelope

# Legacy: These duplicate definitions have been removed to prevent SQLAlchemy registry conflicts
# - Contract is now defined in app.models.contracts and re-exported above
# - ContractEvent is now defined in app.models.contracts and re-exported above
# Use the re-exported versions instead


__all__ = ["Contract", "ContractEvent", "ContractTemplate", "ContractParty", "ContractDocument", "ContractEnvelope"]
