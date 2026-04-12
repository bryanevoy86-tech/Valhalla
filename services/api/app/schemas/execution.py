"""
Schemas for execution layer endpoints - request/response models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class OpportunityIntakeRequest(BaseModel):
    """Raw opportunity input from operator"""
    raw_text: str = Field(..., description="Raw opportunity text/description")
    source_type: Optional[str] = Field(None, description="Hint about input type: email, form, manual_entry, etc")
    
    class Config:
        json_schema_extra = {
            "example": {
                "raw_text": "3bed 2bath house at 123 Main St, asking $250k, needs roof repair",
                "source_type": "manual_entry"
            }
        }


class ProcessIntakeRequest(BaseModel):
    """Request to process an intake record"""
    intake_id: int = Field(..., description="ID of intake to process")
    override_confidence: Optional[float] = Field(None, description="Manually set confidence (0-100)")
    
    class Config:
        json_schema_extra = {
            "example": {"intake_id": 123}
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ExecutionCaseSummary(BaseModel):
    """Complete summary - everything operator needs to know"""
    
    # Identification
    case_id: int
    intake_id: int
    
    # Classification
    classification: str = Field(description="real_estate | business | arbitrage | jv | unknown")
    what_it_is: str = Field(description="Plain language: 'This appears to be a residential wholesale opportunity'")
    
    # Financial
    estimated_value: float = Field(description="Estimated property value (after buffers)")
    estimated_cost: float = Field(description="Estimated total cost (after buffers)")
    estimated_profit: float = Field(description="Profit = value - cost")
    
    # Confidence & Risk
    confidence_level: str = Field(description="low | medium | high")
    confidence_score: float = Field(description="0-100")
    risk_score: float = Field(description="0-100")
    
    # Strategy
    recommended_strategy: str = Field(description="wholesale | fnh | buy_and_hold | jv | etc")
    alternative_strategies: List[str] = Field(description="Other viable strategies")
    
    # Data quality
    missing_information: List[str] = Field(description="Fields needed for higher confidence")
    
    # Execution state
    current_stage: str
    safe_mode: bool = Field(description="If True, operator manual approval required")
    blocked: bool
    blocker_reason: Optional[str]
    
    # Next steps
    next_action: str = Field(description="Clear instruction for operator")
    tasks_created: int = Field(description="How many action items?")
    
    # Metadata
    created_at: datetime
    processing_time_seconds: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "case_id": 1,
                "intake_id": 1,
                "classification": "real_estate",
                "what_it_is": "This appears to be a residential wholesale opportunity",
                "estimated_value": 275000,
                "estimated_cost": 85000,
                "estimated_profit": 45000,
                "confidence_level": "medium",
                "confidence_score": 75,
                "risk_score": 35,
                "recommended_strategy": "wholesale",
                "alternative_strategies": ["fix_and_flip"],
                "missing_information": ["Actual property condition"],
                "current_stage": "tasks_created",
                "safe_mode": False,
                "blocked": False,
                "next_action": "Verify property condition with site visit",
                "tasks_created": 5
            }
        }


class ExecutionTaskOut(BaseModel):
    """Single task for operator"""
    id: int
    case_id: int
    title: str = Field(description="What to do (verb phrase)")
    instructions: str = Field(description="Step-by-step how to do it")
    status: str = Field(description="pending | in_progress | done")
    priority: int = Field(description="1 (urgent) to 10 (low)")
    sequence: int = Field(description="Order in task list")
    category: str = Field(description="verification | contact | analysis | logistics")
    due_at: Optional[datetime]
    guidance_url: Optional[str]
    
    class Config:
        from_attributes = True


class ExecutionTaskListResponse(BaseModel):
    """Operator's task list"""
    case_id: int
    task_count: int
    tasks: List[ExecutionTaskOut]
    
    class Config:
        json_schema_extra = {
            "example": {
                "case_id": 1,
                "task_count": 3,
                "tasks": [
                    {
                        "id": 1,
                        "case_id": 1,
                        "title": "Verify property address",
                        "instructions": "Call county assessor or check MLS",
                        "status": "pending",
                        "priority": 1,
                        "sequence": 1,
                        "category": "verification"
                    }
                ]
            }
        }


class ExecutionNextActionResponse(BaseModel):
    """One clear next action"""
    case_id: int
    action: str = Field(description="What to do now")
    why: str = Field(description="Why this action matters")
    how: str = Field(description="Step-by-step how")
    priority: str = Field(description="urgent | normal | optional")
    blocking: bool = Field(description="Does this block progression?")
    
    class Config:
        json_schema_extra = {
            "example": {
                "case_id": 1,
                "action": "Verify property square footage",
                "why": "Current estimate is from Zillow - need actual to calculate ARV correctly",
                "how": "Contact seller or pull MLS property card for exact SF",
                "priority": "urgent",
                "blocking": True
            }
        }


class ExecutionEventOut(BaseModel):
    """Single event in audit trail"""
    id: int
    case_id: int
    event_type: str
    timestamp: datetime
    actor: str
    description: str
    stage_from: Optional[str]
    stage_to: Optional[str]
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class ExecutionEventLogResponse(BaseModel):
    """Audit trail"""
    case_id: int
    event_count: int
    events: List[ExecutionEventOut]


class CaseStatusResponse(BaseModel):
    """Simple status of a case"""
    case_id: int
    current_stage: str
    current_status: str
    safe_mode: bool
    blocked: bool
    blocker_reason: Optional[str]
    next_action: str
    tasks_pending: int
    tasks_completed: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "case_id": 1,
                "current_stage": "execution",
                "current_status": "in_progress",
                "safe_mode": False,
                "blocked": False,
                "next_action": "Schedule property inspection",
                "tasks_pending": 3,
                "tasks_completed": 2
            }
        }


class AdvanceCaseRequest(BaseModel):
    """Request to advance case to next stage"""
    target_stage: str = Field(description="Stage to advance to")
    operator_notes: Optional[str] = Field(None, description="Operator context/notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "target_stage": "execution",
                "operator_notes": "All verifications complete, ready to proceed"
            }
        }


class AdvanceCaseResponse(BaseModel):
    """Result of advancement"""
    success: bool
    case_id: int
    new_stage: str
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "case_id": 1,
                "new_stage": "execution",
                "message": "Case advanced to execution stage"
            }
        }


class IntakePreview(BaseModel):
    """Preview of intake after creation"""
    intake_id: int
    raw_text: str
    created_at: datetime
    status: str = Field(description="new | normalized | archived")
    message: str = Field(description="Next step for operator")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "intake_id": 1,
                "raw_text": "3bed house at 123 Main...",
                "created_at": "2026-04-12T10:00:00Z",
                "status": "new",
                "message": "Click Process to analyze this opportunity"
            }
        }
