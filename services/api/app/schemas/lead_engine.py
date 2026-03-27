"""
Pydantic schemas for lead acquisition engine.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ===== LEAD SOURCE SCHEMAS =====

class LeadSourceCreate(BaseModel):
    """Create a new lead source"""
    name: str = Field(..., description="Display name")
    source_type: str = Field(..., description="Type: api, scraper, csv, webhook, etc.")
    sector: Optional[str] = Field(None, description="Business sector")
    base_url: Optional[str] = Field(None, description="Base URL for API or scraping")
    scrape_frequency: int = Field(default=24, description="Hours between imports")
    auth_type: str = Field(default="none", description="Authentication method")
    parser_type: str = Field(default="json", description="Parser type: json, csv, html, xml")
    notes: Optional[str] = Field(None, description="Admin notes")


class LeadSourceUpdate(BaseModel):
    """Update a lead source"""
    name: Optional[str] = None
    source_type: Optional[str] = None
    sector: Optional[str] = None
    base_url: Optional[str] = None
    active: Optional[bool] = None
    scrape_frequency: Optional[int] = None
    auth_type: Optional[str] = None
    parser_type: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class LeadSourceResponse(BaseModel):
    """Lead source response"""
    id: int
    name: str
    source_type: str
    sector: Optional[str]
    base_url: Optional[str]
    active: bool
    scrape_frequency: int
    auth_type: str
    parser_type: str
    last_run_at: Optional[datetime]
    last_success_at: Optional[datetime]
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ===== RAW LEAD SCHEMAS =====

class RawLeadCreate(BaseModel):
    """Create raw lead record"""
    source_id: int
    raw_hash: str
    raw_data: dict


class RawLeadResponse(BaseModel):
    """Raw lead response"""
    id: int
    source_id: int
    raw_hash: str
    raw_data: dict
    imported_at: datetime
    status: str
    notes: Optional[str]
    
    class Config:
        from_attributes = True


# ===== NORMALIZED LEAD SCHEMAS =====

class NormalizedLeadCreate(BaseModel):
    """Create normalized lead"""
    source_id: int
    external_id: Optional[str] = None
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    market: Optional[str] = None
    lead_type: Optional[str] = None
    asking_price: Optional[float] = None
    tags: Optional[List[str]] = None


class NormalizedLeadUpdate(BaseModel):
    """Update normalized lead"""
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    market: Optional[str] = None
    lead_type: Optional[str] = None
    asking_price: Optional[float] = None
    tags: Optional[List[str]] = None
    score: Optional[float] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None


class NormalizedLeadResponse(BaseModel):
    """Normalized lead response"""
    id: int
    source_id: int
    external_id: Optional[str]
    full_name: Optional[str]
    company_name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    city: Optional[str]
    market: Optional[str]
    lead_type: Optional[str]
    asking_price: Optional[float]
    tags: List[str]
    score: float
    status: str
    assigned_to: Optional[str]
    duplicate_of: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ===== INGESTION RESPONSE SCHEMAS =====

class IngestionTestResponse(BaseModel):
    """Response from ingestion test endpoint"""
    source_id: int
    source_name: str
    raw_leads_imported: int
    normalized_leads_created: int
    status: str
    message: str
    sample_data: Optional[dict] = None


class LeadListResponse(BaseModel):
    """Response for listing leads"""
    total: int
    items: List[NormalizedLeadResponse]
