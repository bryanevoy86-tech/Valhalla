"""
PACK W: System Status & Metadata Service
Manages system version, completion status, and pack registry.
Marked as stable API (STABLE CONTRACT).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas.system_status import PackInfo
from app.models.system_metadata import SystemMetadata


# Static definition of all packs in the system
_DEFINED_PACKS: List[PackInfo] = [
    # Professional Management Packs (H-R)
    PackInfo(id="H", name="Public Behavioral Signal Extractor", status="installed"),
    PackInfo(id="I", name="Professional Alignment Engine", status="installed"),
    PackInfo(id="J", name="Professional Scorecard Engine", status="installed"),
    PackInfo(id="K", name="Retainer Lifecycle Engine", status="installed"),
    PackInfo(id="L", name="Professional Handoff Engine", status="installed"),
    PackInfo(id="M", name="Professional Task Lifecycle Engine", status="installed"),
    PackInfo(id="N", name="Contract Lifecycle Engine", status="installed"),
    PackInfo(id="O", name="Document Routing Engine", status="installed"),
    PackInfo(id="P", name="Deal Finalization Engine", status="installed"),
    PackInfo(id="Q", name="Internal Auditor (Valhalla)", status="installed"),
    PackInfo(id="R", name="Governance Integration", status="installed"),
    
    # System Infrastructure Packs (S-W)
    PackInfo(id="S", name="System Integration / Debug", status="installed"),
    PackInfo(id="T", name="Production Hardening", status="installed"),
    PackInfo(id="U", name="Frontend API Map", status="installed"),
    PackInfo(id="V", name="Deployment Check / Ops", status="installed"),
    PackInfo(id="W", name="System Completion Metadata", status="installed"),
]

DEFAULT_SUMMARY: str = (
    "Valhalla backend: comprehensive professional services management platform including "
    "professional vetting and scorecards, retainer lifecycle management, task and payment processing, "
    "contract and document management, deal finalization, internal audit and compliance tracking, "
    "governance integration, system debugging and introspection, production hardening with security "
    "middleware, frontend API mapping for auto-generated UI, and deployment readiness automation."
)


def get_system_metadata(db: Session) -> Optional[SystemMetadata]:
    """
    Retrieve system metadata from database.
    
    Args:
        db: Database session
    
    Returns:
        SystemMetadata if exists, None otherwise
    """
    return db.query(SystemMetadata).filter(SystemMetadata.id == 1).first()


def ensure_system_metadata(db: Session) -> SystemMetadata:
    """
    Ensure system metadata row exists, creating with defaults if needed.
    
    STABLE CONTRACT: Initialization values will not change.
    
    Args:
        db: Database session
    
    Returns:
        SystemMetadata: The existing or newly created metadata row
    """
    meta = get_system_metadata(db)
    
    if not meta:
        meta = SystemMetadata(
            id=1,
            version="1.0.0",
            backend_complete=False,
            notes="System metadata initialized.",
            updated_at=datetime.utcnow(),
        )
        db.add(meta)
        db.commit()
        db.refresh(meta)
    
    return meta


def get_packs() -> List[Dict[str, Any]]:
    """
    Get list of all installed packs.
    
    STABLE CONTRACT: Pack registry will not change in breaking ways.
    
    Returns:
        List of pack definitions as dicts
    """
    return [pack.dict() for pack in _DEFINED_PACKS]


def get_system_status(db: Session) -> Dict[str, Any]:
    """
    Get complete system status including version, completion flag, and pack list.
    
    STABLE CONTRACT: Response format and keys will not change.
    
    Args:
        db: Database session
    
    Returns:
        Dict with keys: version, backend_complete, packs, summary, extra
    """
    meta = ensure_system_metadata(db)
    
    return {
        "version": meta.version,
        "backend_complete": meta.backend_complete,
        "packs": get_packs(),
        "summary": DEFAULT_SUMMARY,
        "extra": {
            "notes": meta.notes,
            "updated_at": meta.updated_at.isoformat() if meta.updated_at else None,
            "completed_at": meta.completed_at.isoformat() if meta.completed_at else None,
        },
    }


def set_backend_complete(
    db: Session,
    flag: bool = True,
    notes: Optional[str] = None,
) -> SystemMetadata:
    """
    Set or unset the backend_complete flag.
    
    If setting to True, records completion timestamp.
    If setting to False, clears completion timestamp (development mode).
    
    STABLE CONTRACT: Behavior will not change.
    
    Args:
        db: Database session
        flag: True to mark complete, False to mark incomplete
        notes: Optional notes about the status change
    
    Returns:
        Updated SystemMetadata
    """
    meta = ensure_system_metadata(db)
    
    meta.backend_complete = flag
    
    # Update notes if provided
    if notes is not None:
        meta.notes = notes
    
    # Record completion timestamp when marking complete
    if flag and not meta.completed_at:
        meta.completed_at = datetime.utcnow()
    
    # Clear completion timestamp if unmarking
    if not flag:
        meta.completed_at = None
    
    meta.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(meta)
    
    return meta


def update_version(
    db: Session,
    new_version: str,
    notes: Optional[str] = None,
) -> SystemMetadata:
    """
    Update system version.
    
    STABLE CONTRACT: Version update will not change in breaking ways.
    
    Args:
        db: Database session
        new_version: New semantic version string
        notes: Optional notes about the version update
    
    Returns:
        Updated SystemMetadata
    """
    meta = ensure_system_metadata(db)
    
    meta.version = new_version
    
    if notes is not None:
        meta.notes = notes
    
    meta.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(meta)
    
    return meta


def get_pack_by_id(pack_id: str) -> Optional[PackInfo]:
    """
    Get a specific pack by ID.
    
    Args:
        pack_id: Pack identifier (A-Z)
    
    Returns:
        PackInfo if found, None otherwise
    """
    for pack in _DEFINED_PACKS:
        if pack.id == pack_id:
            return pack
    return None


def count_packs_by_status(status: str) -> int:
    """
    Count packs with a given status.
    
    Args:
        status: Status to count (installed, pending, deprecated, experimental)
    
    Returns:
        Number of packs with that status
    """
    return sum(1 for pack in _DEFINED_PACKS if pack.status == status)


def get_system_summary() -> Dict[str, Any]:
    """
    Get high-level system summary without database queries.
    
    Useful for health checks or quick status without DB overhead.
    
    STABLE CONTRACT: Response format will not change.
    
    Returns:
        Dict with pack counts and summary description
    """
    return {
        "total_packs": len(_DEFINED_PACKS),
        "installed_packs": count_packs_by_status("installed"),
        "pending_packs": count_packs_by_status("pending"),
        "deprecated_packs": count_packs_by_status("deprecated"),
        "summary": DEFAULT_SUMMARY,
    }
