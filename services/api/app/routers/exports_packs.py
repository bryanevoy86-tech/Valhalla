"""
PACK-REPORT: EIA Export & Appointment Pack Router

Endpoints for managing EIA months, appointment packs, and generating export packages.
"""

from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os

from app.core.db import get_db
from app.services.eia_export import (
    close_eia_month,
    open_eia_month,
    get_or_create_eia_month,
    generate_eia_pack,
    generate_accountant_pack,
    generate_legal_pack,
    generate_appointment_pack,
)
from app.schemas.eia_export import (
    MonthCloseResponse,
    MonthOpenResponse,
    EIAExportPackResponse,
    AccountantExportPackResponse,
    LegalExportPackResponse,
    AppointmentPackResponse,
)


router = APIRouter(
    prefix="/exports/packs",
    tags=["Exports & Packs"]
)


# ============================================================================
# Pack Generation Endpoints
# ============================================================================

@router.post("/eia", response_model=EIAExportPackResponse)
async def generate_eia_export(
    year: int,
    month: int,
    db: Session = Depends(get_db),
) -> EIAExportPackResponse:
    """
    Generate EIA export package.
    
    Creates or retrieves the month, then generates the EIA-compliant export
    package containing monthly financial summary, disbursements, and evidence index.
    
    Args:
        year: The fiscal year (e.g., 2026)
        month: The month number (1-12)
        db: Database session
    
    Returns:
        EIAExportPackResponse with package data
    """
    eia_month = get_or_create_eia_month(db, year, month)
    return generate_eia_pack(db, eia_month)


@router.post("/accountant", response_model=AccountantExportPackResponse)
async def generate_accountant_export(
    year: int,
    month: int,
    db: Session = Depends(get_db),
) -> AccountantExportPackResponse:
    """
    Generate accountant export package.
    
    Creates or retrieves the month, then generates the accountant-ready package
    containing financial summary, disbursements, evidence index, and compliance checklist.
    
    Args:
        year: The fiscal year (e.g., 2026)
        month: The month number (1-12)
        db: Database session
    
    Returns:
        AccountantExportPackResponse with package data
    """
    eia_month = get_or_create_eia_month(db, year, month)
    return generate_accountant_pack(db, eia_month)


@router.post("/legal", response_model=LegalExportPackResponse)
async def generate_legal_export(
    year: int,
    month: int,
    db: Session = Depends(get_db),
) -> LegalExportPackResponse:
    """
    Generate legal document pack.
    
    Creates or retrieves the month, then generates the legal package
    containing contractual templates and agreements for review.
    
    Args:
        year: The fiscal year (e.g., 2026)
        month: The month number (1-12)
        db: Database session
    
    Returns:
        LegalExportPackResponse with package data
    """
    eia_month = get_or_create_eia_month(db, year, month)
    return generate_legal_pack(db, eia_month)


@router.post("/appointment/eia", response_model=AppointmentPackResponse)
async def generate_appointment_export(
    year: int,
    month: int,
    include_business_plan: bool = False,
    db: Session = Depends(get_db),
) -> AppointmentPackResponse:
    """
    Generate appointment-ready bundle.
    
    Creates or retrieves the month, then generates a complete appointment package
    combining EIA, accountant, and legal packs. Optionally includes business plan.
    
    Args:
        year: The fiscal year (e.g., 2026)
        month: The month number (1-12)
        include_business_plan: Optional flag to include business plan in bundle
        db: Database session
    
    Returns:
        AppointmentPackResponse with all sub-packages
    """
    eia_month = get_or_create_eia_month(db, year, month)
    return generate_appointment_pack(db, eia_month, include_business_plan)


@router.post("/appointment/eia/close", response_model=MonthCloseResponse)
async def close_appointment_eia(
    year: int,
    month: int,
    locked_by: str = "system",
    db: Session = Depends(get_db),
) -> MonthCloseResponse:
    """
    Close and lock an EIA month for appointment pack generation.
    
    Once a month is locked, it can be exported to appointment packs.
    The month will be frozen with a lock receipt containing timestamp, 
    user, and warnings snapshot.
    
    Args:
        year: The fiscal year (e.g., 2026)
        month: The month number (1-12)
        locked_by: User/system identifier who is locking the month
        db: Database session
    
    Returns:
        MonthCloseResponse with lock receipt properly serialized as dict
    """
    return close_eia_month(db, year, month, locked_by)


@router.post("/appointment/eia/ensure-close", response_model=MonthCloseResponse)
async def ensure_close_appointment_eia(
    year: int,
    month: int,
    locked_by: str = "system",
    db: Session = Depends(get_db),
) -> MonthCloseResponse:
    """
    Idempotent close operation for EIA month appointment pack.
    
    Ensures the month is closed without error if already closed.
    Returns success=True whether month was just locked or was already locked.
    
    Args:
        year: The fiscal year (e.g., 2026)
        month: The month number (1-12)
        locked_by: User/system identifier who is locking the month
        db: Database session
    
    Returns:
        MonthCloseResponse with lock receipt properly serialized as dict
    """
    result = close_eia_month(db, year, month, locked_by)
    
    # Ensure-close is idempotent: if already locked, treat as success
    if not result.success and "already locked" in result.message.lower():
        result.success = True
        result.message = f"Month {year}-{month:02d} is locked (already closed)"
    
    return result


# ============================================================================
# File Download/Retrieval Endpoints
# ============================================================================

def _get_safe_export_path(package_type: str, year: int, month: int) -> Path:
    """
    Safely resolve generated export file path.
    
    Constructs and validates path to prevent traversal attacks.
    File must exist within generated_exports/ directory.
    
    Args:
        package_type: Type of pack (eia, accountant, legal, appointment)
        year: Fiscal year
        month: Month number (1-12)
    
    Returns:
        Path object pointing to generated file
    
    Raises:
        HTTPException: If file doesn't exist or path is invalid
    """
    # Get the base app directory: __file__ = app/routers/exports_packs.py
    # So parent.parent = services/api
    router_file = Path(__file__)
    base_dir = router_file.parent.parent.parent  # services/api
    base_exports_dir = base_dir / "generated_exports"
    
    # Construct filename with strict naming pattern
    filename = f"{package_type}_pack_{year}_{month:02d}.zip"
    file_path = base_exports_dir / filename
    
    # Security check: ensure file is within generated_exports directory
    try:
        file_path.resolve().relative_to(base_exports_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    # Check if file exists
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Export file not found: {package_type} pack for {year}-{month:02d}"
        )
    
    return file_path


@router.get("/download")
async def download_export_pack(
    package_type: str,
    year: int,
    month: int,
) -> FileResponse:
    """
    Download a generated export package ZIP file.
    
    Retrieves a previously generated pack file and returns it as a downloadable attachment.
    
    Args:
        package_type: Type of pack - must be one of: eia, accountant, legal, appointment
        year: Fiscal year (e.g., 2026)
        month: Month number (1-12)
    
    Returns:
        FileResponse containing the ZIP file
    
    Raises:
        HTTPException 400: If package_type or parameters are invalid
        HTTPException 404: If file doesn't exist
    """
    # Validate package_type
    valid_types = ["eia", "accountant", "legal", "appointment"]
    if package_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid package_type. Must be one of: {', '.join(valid_types)}"
        )
    
    # Validate month range
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    # Get safe file path
    file_path = _get_safe_export_path(package_type, year, month)
    
    # Return file with appropriate content type and filename
    filename = f"{package_type}_pack_{year}_{month:02d}.zip"
    return FileResponse(
        path=file_path,
        media_type="application/zip",
        filename=filename
    )


@router.get("/files")
async def list_export_files(
    year: int,
    month: int,
) -> dict:
    """
    List available generated export files for a given month.
    
    Returns metadata about all generated packs for the specified year/month.
    
    Args:
        year: Fiscal year (e.g., 2026)
        month: Month number (1-12)
    
    Returns:
        Dictionary with available packs and their metadata
    """
    # Validate month range
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    router_file = Path(__file__)
    base_dir = router_file.parent.parent.parent  # services/api
    base_exports_dir = base_dir / "generated_exports"
    
    available_files = {}
    
    for package_type in ["eia", "accountant", "legal", "appointment"]:
        try:
            file_path = _get_safe_export_path(package_type, year, month)
            file_size = file_path.stat().st_size
            available_files[package_type] = {
                "filename": f"{package_type}_pack_{year}_{month:02d}.zip",
                "size_bytes": file_size,
                "download_url": f"/exports/packs/download?package_type={package_type}&year={year}&month={month}"
            }
        except HTTPException:
            # File doesn't exist for this type, skip it
            pass
    
    return {
        "year": year,
        "month": month,
        "available_packs": available_files,
        "count": len(available_files)
    }
