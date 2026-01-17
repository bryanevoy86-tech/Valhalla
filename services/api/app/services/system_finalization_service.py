"""PACK 60: System Finalization Service
Service layer for system integrity sealing.
"""

import hashlib
from sqlalchemy.orm import Session

from app.models.system_finalization import SystemIntegritySeal


def generate_integrity_hash(schema_version: str) -> str:
    """Generate integrity hash from schema version."""
    payload = f"valhalla|{schema_version}"
    return hashlib.sha256(payload.encode()).hexdigest()


def create_integrity_seal(db: Session, schema_version: str) -> SystemIntegritySeal:
    """Create a new system integrity seal."""
    seal_hash = generate_integrity_hash(schema_version)
    seal = SystemIntegritySeal(
        seal_hash=seal_hash,
        schema_version=schema_version,
        active=True
    )
    db.add(seal)
    db.commit()
    db.refresh(seal)
    return seal


def deactivate_previous_seals(db: Session) -> None:
    """Deactivate all previous seals."""
    db.query(SystemIntegritySeal).update({"active": False})
    db.commit()
