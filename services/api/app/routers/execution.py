"""
Execution Router - Operator interface for the execution layer
7 simple endpoints: Paste → Process → Guide → Advance
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import logging

from app.core.db import get_db
from app.models.lead_intake import LeadIntake
from app.models.task import Task
from app.models.execution_case import ExecutionCase
from app.models.execution_event import ExecutionEvent
from app.schemas.execution import (
    OpportunityIntakeRequest,
    ProcessIntakeRequest,
    ExecutionCaseSummary,
    ExecutionTaskListResponse,
    ExecutionTaskOut,
    ExecutionNextActionResponse,
    ExecutionEventLogResponse,
    ExecutionEventOut,
    CaseStatusResponse,
    AdvanceCaseRequest,
    AdvanceCaseResponse,
    IntakePreview,
)
from app.services.intake_parser_service import IntakeParserService
from app.services.opportunity_classifier_service import OpportunityClassifier
from app.services.execution_assessment_service import ExecutionAssessmentService
from app.services.routing_service import RoutingService
from app.services.task_generation_service import ExecutionTaskGenerationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/execution", tags=["execution"])


# ============================================================================
# ENDPOINT 1: POST /execution/intake - Paste opportunity
# ============================================================================

@router.post("/intake", response_model=IntakePreview)
def create_intake(
    request: OpportunityIntakeRequest,
    db: Session = Depends(get_db),
):
    """
    Operator pastes raw opportunity text.
    Returns intake ID to use in next step.
    
    Simple workflow:
    1. Paste raw text from email, form, or manual notes
    2. System creates intake record
    3. Operator clicks "Process" with the intake_id
    """
    
    try:
        # Create LeadIntake record (existing model)
        intake = LeadIntake(
            raw_text=request.raw_text[:2000],  # Truncate if too long
            source_type=request.source_type or "manual_entry",
            status="new",
        )
        db.add(intake)
        db.commit()
        db.refresh(intake)
        
        return IntakePreview(
            intake_id=intake.id,
            raw_text=intake.raw_text,
            created_at=intake.created_at,
            status="new",
            message="✓ Opportunity recorded. Click Process to analyze.",
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Intake creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create intake: {str(e)}"
        )


# ============================================================================
# ENDPOINT 2: POST /execution/intake/{id}/process - Analyze opportunity
# ============================================================================

@router.post("/intake/{intake_id}/process", response_model=ExecutionCaseSummary)
def process_intake(
    intake_id: int,
    request: ProcessIntakeRequest,
    db: Session = Depends(get_db),
):
    """
    Process intake through full pipeline:
    1. Parse raw text
    2. Classify opportunity type
    3. Apply conservative assessment
    4. Route to execution pipeline
    5. Generate task list
    6. Return complete summary for operator
    
    This is the core processing engine.
    """
    
    try:
        # Load intake
        intake = db.query(LeadIntake).filter(LeadIntake.id == intake_id).first()
        if not intake:
            raise HTTPException(status_code=404, detail="Intake not found")
        
        start_time = datetime.utcnow()
        
        # Step 1: Parse
        parser = IntakeParserService()
        parsed = parser.parse(intake.raw_text)
        extracted_fields = parsed["extracted_fields"]
        
        # Step 2: Classify
        classifier = OpportunityClassifier()
        classification, clf_details = classifier.classify(intake.raw_text)
        
        # Step 3: Assess with conservative buffers
        assessor = ExecutionAssessmentService(db)
        
        # Prepare raw estimate from extracted fields
        raw_estimate = {
            "arv_estimate": extracted_fields.get("estimated_arv") or extracted_fields.get("asking_price") * 1.2,
            "repair_estimate": extracted_fields.get("estimated_repair_cost") or 0,
            "purchase_price": extracted_fields.get("asking_price") or 0,
            "operating_cost": extracted_fields.get("operating_cost") or 0,
        }
        
        # Override confidence if provided
        confidence_input = request.override_confidence or clf_details.get("confidence", 50)
        assessment = assessor.assess_real_estate_deal(raw_estimate, confidence=confidence_input)
        
        # Step 4: Route
        router_svc = RoutingService()
        routing = router_svc.route(
            classification=classification,
            assessment=assessment,
            extracted_fields=extracted_fields,
        )
        
        # Step 5: Create ExecutionCase
        case = ExecutionCase(
            intake_id=intake_id,
            case_type=classification,
            route_target=routing["pipeline"],
            current_stage="intake_processed",
            current_status="pending_review",
            safe_mode=assessment.get("safe_mode", False),
            blocked=assessment.get("blocked", False),
            blocker_reason=assessment.get("reason"),
            next_action=routing.get("reasoning", "Review and decide"),
            created_by="system",
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        
        # Step 6: Generate tasks
        task_gen = ExecutionTaskGenerationService()
        task_specs = task_gen.generate_tasks(
            case_id=case.id,
            pipeline=routing["pipeline"],
            classification=classification,
            assessment=assessment,
            extracted_fields=extracted_fields,
            missing_fields=parsed["missing_fields"],
        )
        
        # Create Task records
        for spec in task_specs:
            task = Task(
                case_id=case.id,
                title=spec["title"],
                description=spec.get("instructions", ""),
                status=spec.get("status", "pending"),
                priority=spec.get("priority", 5),
                sequence=spec.get("sequence", 0),
                category=spec.get("category", "execution"),
                due_days=spec.get("due_days", 7),
            )
            db.add(task)
        db.commit()
        
        # Log event
        event = ExecutionEvent(
            case_id=case.id,
            event_type="intake_processed",
            stage_from="intake",
            stage_to="intake_processed",
            action_description="Intake processed through full pipeline",
            payload_json=str({
                "parsed_fields": parsed["extracted_fields"],
                "classification": classification,
                "assessment": assessment,
                "routing": routing,
            }),
            actor="system",
        )
        db.add(event)
        db.commit()
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Build response
        return ExecutionCaseSummary(
            case_id=case.id,
            intake_id=intake_id,
            classification=classification,
            what_it_is=clf_details.get("reasoning", "Unknown opportunity"),
            estimated_value=assessment.get("estimated_value", 0),
            estimated_cost=assessment.get("estimated_purchase_cost", 0),
            estimated_profit=assessment.get("estimated_profit", 0),
            confidence_level=assessment.get("confidence_level", "low"),
            confidence_score=assessment.get("confidence_score", 0),
            risk_score=assessment.get("risk_score", 50),
            recommended_strategy=routing.get("pipeline", "unknown"),
            alternative_strategies=routing.get("alternative_strategies", []),
            missing_information=parsed.get("missing_fields", []),
            current_stage=case.current_stage,
            safe_mode=case.safe_mode,
            blocked=case.blocked,
            blocker_reason=case.blocker_reason,
            next_action=case.next_action,
            tasks_created=len(task_specs),
            created_at=case.created_at,
            processing_time_seconds=processing_time,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Process intake failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


# ============================================================================
# ENDPOINT 3: GET /execution/cases/{case_id} - Get complete case summary
# ============================================================================

@router.get("/cases/{case_id}", response_model=ExecutionCaseSummary)
def get_case_summary(
    case_id: int,
    db: Session = Depends(get_db),
):
    """
    Get complete case summary - everything operator needs to know.
    """
    
    try:
        case = db.query(ExecutionCase).filter(ExecutionCase.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        intake = db.query(LeadIntake).filter(LeadIntake.id == case.intake_id).first()
        
        # For now, return cached summary or re-calculate
        return ExecutionCaseSummary(
            case_id=case.id,
            intake_id=case.intake_id,
            classification=case.case_type,
            what_it_is=f"Opportunity classified as {case.case_type}",
            estimated_value=0,  # Would load from assessment
            estimated_cost=0,
            estimated_profit=0,
            confidence_level="medium",
            confidence_score=75,
            risk_score=40,
            recommended_strategy=case.route_target,
            alternative_strategies=[],
            missing_information=[],
            current_stage=case.current_stage,
            safe_mode=case.safe_mode,
            blocked=case.blocked,
            blocker_reason=case.blocker_reason,
            next_action=case.next_action,
            tasks_created=0,
            created_at=case.created_at,
            processing_time_seconds=0,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get case summary failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve case: {str(e)}"
        )


# ============================================================================
# ENDPOINT 4: GET /execution/cases/{case_id}/tasks - Get operator task list
# ============================================================================

@router.get("/cases/{case_id}/tasks", response_model=ExecutionTaskListResponse)
def get_case_tasks(
    case_id: int,
    db: Session = Depends(get_db),
):
    """
    Get operator's task list for a case.
    """
    
    try:
        case = db.query(ExecutionCase).filter(ExecutionCase.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        tasks = db.query(Task).filter(Task.case_id == case_id).order_by(Task.sequence).all()
        
        task_list = [
            ExecutionTaskOut(
                id=t.id,
                case_id=t.case_id,
                title=t.title,
                instructions=t.description,
                status=t.status,
                priority=t.priority,
                sequence=t.sequence,
                category=t.category,
                due_at=None,  # Would calculate from due_days
                guidance_url=None,
            )
            for t in tasks
        ]
        
        return ExecutionTaskListResponse(
            case_id=case_id,
            task_count=len(task_list),
            tasks=task_list,
        )
    
    except Exception as e:
        logger.error(f"Get tasks failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tasks: {str(e)}"
        )


# ============================================================================
# ENDPOINT 5: GET /execution/cases/{case_id}/next-action - Simple next step
# ============================================================================

@router.get("/cases/{case_id}/next-action", response_model=ExecutionNextActionResponse)
def get_next_action(
    case_id: int,
    db: Session = Depends(get_db),
):
    """
    Get one clear next action for operator.
    No decisions, no thinking required.
    """
    
    try:
        case = db.query(ExecutionCase).filter(ExecutionCase.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Get next pending task
        next_task = db.query(Task).filter(
            Task.case_id == case_id,
            Task.status == "pending"
        ).order_by(Task.sequence).first()
        
        if not next_task:
            action = "Review case and decide to proceed or pass"
            why = "All verification tasks complete"
            how = "Review all information and click Advance"
            priority = "normal"
            blocking = False
        else:
            action = next_task.title
            why = f"This is required to proceed (priority {next_task.priority})"
            how = next_task.description
            priority = "urgent" if next_task.priority < 3 else "normal"
            blocking = next_task.priority < 3
        
        return ExecutionNextActionResponse(
            case_id=case_id,
            action=action,
            why=why,
            how=how,
            priority=priority,
            blocking=blocking,
        )
    
    except Exception as e:
        logger.error(f"Get next action failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve next action: {str(e)}"
        )


# ============================================================================
# ENDPOINT 6: POST /execution/cases/{case_id}/advance - Move case forward
# ============================================================================

@router.post("/cases/{case_id}/advance", response_model=AdvanceCaseResponse)
def advance_case(
    case_id: int,
    request: AdvanceCaseRequest,
    db: Session = Depends(get_db),
):
    """
    Advance case to next stage.
    Only allowed if safe_mode not blocking.
    """
    
    try:
        case = db.query(ExecutionCase).filter(ExecutionCase.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        if case.blocked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Case is blocked: {case.blocker_reason}"
            )
        
        if case.safe_mode:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Safe mode active - manual approval required"
            )
        
        # Record old stage
        old_stage = case.current_stage
        
        # Update case
        case.current_stage = request.target_stage
        case.updated_at = datetime.utcnow()
        case.updated_by = "operator"
        
        db.add(case)
        db.commit()
        db.refresh(case)
        
        # Log event
        event = ExecutionEvent(
            case_id=case_id,
            event_type="case_advanced",
            stage_from=old_stage,
            stage_to=request.target_stage,
            action_description=request.operator_notes or "Case advanced",
            payload_json=str({"stage_from": old_stage, "stage_to": request.target_stage}),
            actor="operator",
        )
        db.add(event)
        db.commit()
        
        return AdvanceCaseResponse(
            success=True,
            case_id=case_id,
            new_stage=case.current_stage,
            message=f"Case advanced to {request.target_stage}",
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Advance case failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to advance case: {str(e)}"
        )


# ============================================================================
# ENDPOINT 7: GET /execution/cases/{case_id}/events - Audit trail
# ============================================================================

@router.get("/cases/{case_id}/events", response_model=ExecutionEventLogResponse)
def get_case_events(
    case_id: int,
    db: Session = Depends(get_db),
):
    """
    Get complete audit trail for a case.
    """
    
    try:
        case = db.query(ExecutionCase).filter(ExecutionCase.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        events = db.query(ExecutionEvent).filter(
            ExecutionEvent.case_id == case_id
        ).order_by(desc(ExecutionEvent.created_at)).all()
        
        event_list = [
            ExecutionEventOut(
                id=e.id,
                case_id=e.case_id,
                event_type=e.event_type,
                timestamp=e.created_at,
                actor=e.actor,
                description=e.action_description,
                stage_from=e.stage_from,
                stage_to=e.stage_to,
                payload=e.payload_json or {},
            )
            for e in events
        ]
        
        return ExecutionEventLogResponse(
            case_id=case_id,
            event_count=len(event_list),
            events=event_list,
        )
    
    except Exception as e:
        logger.error(f"Get events failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve events: {str(e)}"
        )
