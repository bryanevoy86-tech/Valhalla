"""
Pydantic schemas for EIA export and pack generation
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MonthCloseResponse(BaseModel):
    """Response when closing an EIA month"""
    year: int
    month: int
    status: str
    locked: bool
    locked_by: str
    locked_at: str


class MonthOpenResponse(BaseModel):
    """Response when opening an EIA month"""
    year: int
    month: int
    status: str
    locked: bool
    opened_by: str
    opened_at: str


class MonthStatusResponse(BaseModel):
    """Status of an EIA month"""
    year: int
    month: int
    status: str
    locked: bool
    ready_for_export: bool


class EIAExportPackResponse(BaseModel):
    """Response from generating an EIA export pack"""
    year: int
    month: int
    package_type: str
    file_path: str
    filename: str
    generated_at: str


class AccountantExportPackResponse(BaseModel):
    """Response from generating an accountant export pack"""
    year: int
    month: int
    package_type: str
    file_path: str
    filename: str
    generated_at: str


class LegalExportPackResponse(BaseModel):
    """Response from generating a legal export pack"""
    year: int
    month: int
    package_type: str
    file_path: str
    filename: str
    generated_at: str


class AppointmentPackResponse(BaseModel):
    """Response from generating an appointment/closing pack"""
    year: int
    month: int
    package_type: str
    file_path: str
    filename: str
    generated_at: str


class FileListResponse(BaseModel):
    """List of exported files"""
    year: int
    month: int
    files: list[dict]


class DownloadPackageResponse(BaseModel):
    """Details about a downloadable package"""
    filename: str
    size: int
    content_type: str
