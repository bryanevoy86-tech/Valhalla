"""
PACK SB: Business Registration Navigator Schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class RegistrationFlowStepSchema(BaseModel):
    step_id: str
    category: str = Field(..., description="naming, structure, documents, accounts, tax_numbers")
    description: str
    required_documents: Optional[List[Dict[str, str]]] = None
    status: str = Field(default="pending")
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class RegistrationStageTrackerSchema(BaseModel):
    current_stage: str = Field(default="preparation")
    business_name: Optional[str] = None
    business_description: Optional[str] = None
    founders_list: Optional[List[Dict[str, Any]]] = None
    selected_structure: Optional[str] = None
    structure_notes: Optional[str] = None
    founder_ids_uploaded: bool = False
    purpose_statement: Optional[str] = None
    naics_codes: Optional[List[str]] = None
    business_address: Optional[str] = None
    filing_completed: bool = False
    filing_receipt_uploaded: bool = False
    registration_number: Optional[str] = None
    articles_uploaded: bool = False
    incorporation_docs_uploaded: bool = False
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class StageProgressResponse(BaseModel):
    current_stage: str
    completed_stages: List[str]
    next_stage: str
    progress_percentage: float
    missing_items: List[str]
