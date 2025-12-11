"""
FastAPI routers for PACK ST, SU, SV

REST API endpoints for financial stress, personal safety, and empire growth.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.schemas.pack_st_su_sv import (
    FinancialIndicatorCreate, FinancialIndicatorUpdate, FinancialIndicatorResponse,
    FinancialStressEventCreate, FinancialStressEventUpdate, FinancialStressEventResponse,
    FinancialStressSummaryCreate, FinancialStressSummaryUpdate, FinancialStressSummaryResponse,
    SafetyCategoryCreate, SafetyCategoryUpdate, SafetyCategoryResponse,
    SafetyChecklistCreate, SafetyChecklistUpdate, SafetyChecklistResponse,
    SafetyPlanCreate, SafetyPlanUpdate, SafetyPlanResponse,
    SafetyEventLogCreate, SafetyEventLogResponse,
    EmpireGoalCreate, EmpireGoalUpdate, EmpireGoalResponse,
    GoalMilestoneCreate, GoalMilestoneUpdate, GoalMilestoneResponse,
    ActionStepCreate, ActionStepUpdate, ActionStepResponse
)
from app.services.pack_st_su_sv import (
    FinancialIndicatorService, FinancialStressEventService, FinancialStressSummaryService,
    SafetyCategoryService, SafetyChecklistService, SafetyPlanService, SafetyEventLogService,
    EmpireGoalService, GoalMilestoneService, ActionStepService
)


# ============================================================================
# PACK ST: Financial Stress Early Warning Engine Router
# ============================================================================

router_st = APIRouter(prefix="/api/v1/financial", tags=["Financial Stress"])


# Financial Indicators
@router_st.post("/indicators", response_model=FinancialIndicatorResponse, status_code=status.HTTP_201_CREATED)
def create_indicator(data: FinancialIndicatorCreate, db: Session = Depends(get_db)):
    """Create a new financial indicator."""
    return FinancialIndicatorService.create(db, data)


@router_st.get("/indicators", response_model=List[FinancialIndicatorResponse])
def list_indicators(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all financial indicators."""
    return FinancialIndicatorService.list_all(db, skip, limit)


@router_st.get("/indicators/{indicator_id}", response_model=FinancialIndicatorResponse)
def get_indicator(indicator_id: int, db: Session = Depends(get_db)):
    """Get a specific indicator."""
    indicator = FinancialIndicatorService.get(db, indicator_id)
    if not indicator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indicator not found")
    return indicator


@router_st.put("/indicators/{indicator_id}", response_model=FinancialIndicatorResponse)
def update_indicator(indicator_id: int, data: FinancialIndicatorUpdate, db: Session = Depends(get_db)):
    """Update a financial indicator."""
    indicator = FinancialIndicatorService.update(db, indicator_id, data)
    if not indicator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indicator not found")
    return indicator


@router_st.delete("/indicators/{indicator_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_indicator(indicator_id: int, db: Session = Depends(get_db)):
    """Delete a financial indicator."""
    if not FinancialIndicatorService.delete(db, indicator_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indicator not found")


# Financial Stress Events
@router_st.post("/events", response_model=FinancialStressEventResponse, status_code=status.HTTP_201_CREATED)
def create_event(data: FinancialStressEventCreate, db: Session = Depends(get_db)):
    """Create a new stress event."""
    return FinancialStressEventService.create(db, data)


@router_st.get("/events/{event_id}", response_model=FinancialStressEventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get a specific event."""
    event = FinancialStressEventService.get(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router_st.get("/indicators/{indicator_id}/events", response_model=List[FinancialStressEventResponse])
def list_indicator_events(indicator_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all events for an indicator."""
    return FinancialStressEventService.list_by_indicator(db, indicator_id, skip, limit)


@router_st.put("/events/{event_id}", response_model=FinancialStressEventResponse)
def update_event(event_id: int, data: FinancialStressEventUpdate, db: Session = Depends(get_db)):
    """Update a stress event."""
    event = FinancialStressEventService.update(db, event_id, data)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


# Financial Stress Summaries
@router_st.post("/summaries", response_model=FinancialStressSummaryResponse, status_code=status.HTTP_201_CREATED)
def create_summary(data: FinancialStressSummaryCreate, db: Session = Depends(get_db)):
    """Create a financial stress summary."""
    return FinancialStressSummaryService.create(db, data)


@router_st.get("/summaries", response_model=List[FinancialStressSummaryResponse])
def list_summaries(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all financial stress summaries."""
    return FinancialStressSummaryService.list_all(db, skip, limit)


@router_st.get("/summaries/{summary_id}", response_model=FinancialStressSummaryResponse)
def get_summary(summary_id: int, db: Session = Depends(get_db)):
    """Get a specific summary."""
    summary = FinancialStressSummaryService.get(db, summary_id)
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found")
    return summary


@router_st.get("/summaries/month/{month}", response_model=FinancialStressSummaryResponse)
def get_summary_by_month(month: str, db: Session = Depends(get_db)):
    """Get summary for a specific month (YYYY-MM)."""
    summary = FinancialStressSummaryService.get_by_month(db, month)
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found")
    return summary


@router_st.put("/summaries/{summary_id}", response_model=FinancialStressSummaryResponse)
def update_summary(summary_id: int, data: FinancialStressSummaryUpdate, db: Session = Depends(get_db)):
    """Update a financial stress summary."""
    summary = FinancialStressSummaryService.update(db, summary_id, data)
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found")
    return summary


# ============================================================================
# PACK SU: Personal Safety & Risk Mitigation Planner Router
# ============================================================================

router_su = APIRouter(prefix="/api/v1/safety", tags=["Personal Safety"])


# Safety Categories
@router_su.post("/categories", response_model=SafetyCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(data: SafetyCategoryCreate, db: Session = Depends(get_db)):
    """Create a new safety category."""
    return SafetyCategoryService.create(db, data)


@router_su.get("/categories", response_model=List[SafetyCategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    """List all safety categories."""
    return SafetyCategoryService.list_all(db)


@router_su.get("/categories/{category_id}", response_model=SafetyCategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get a specific category."""
    category = SafetyCategoryService.get(db, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router_su.put("/categories/{category_id}", response_model=SafetyCategoryResponse)
def update_category(category_id: int, data: SafetyCategoryUpdate, db: Session = Depends(get_db)):
    """Update a safety category."""
    category = SafetyCategoryService.update(db, category_id, data)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router_su.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Delete a safety category."""
    if not SafetyCategoryService.delete(db, category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")


# Safety Checklists
@router_su.post("/checklists", response_model=SafetyChecklistResponse, status_code=status.HTTP_201_CREATED)
def create_checklist(data: SafetyChecklistCreate, db: Session = Depends(get_db)):
    """Create a new safety checklist item."""
    return SafetyChecklistService.create(db, data)


@router_su.get("/checklists/{checklist_id}", response_model=SafetyChecklistResponse)
def get_checklist(checklist_id: int, db: Session = Depends(get_db)):
    """Get a specific checklist item."""
    checklist = SafetyChecklistService.get(db, checklist_id)
    if not checklist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist not found")
    return checklist


@router_su.get("/categories/{category_id}/checklists", response_model=List[SafetyChecklistResponse])
def list_category_checklists(category_id: int, db: Session = Depends(get_db)):
    """List checklists for a category."""
    return SafetyChecklistService.list_by_category(db, category_id)


@router_su.put("/checklists/{checklist_id}", response_model=SafetyChecklistResponse)
def update_checklist(checklist_id: int, data: SafetyChecklistUpdate, db: Session = Depends(get_db)):
    """Update a safety checklist item."""
    checklist = SafetyChecklistService.update(db, checklist_id, data)
    if not checklist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist not found")
    return checklist


@router_su.delete("/checklists/{checklist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_checklist(checklist_id: int, db: Session = Depends(get_db)):
    """Delete a safety checklist item."""
    if not SafetyChecklistService.delete(db, checklist_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist not found")


# Safety Plans
@router_su.post("/plans", response_model=SafetyPlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(data: SafetyPlanCreate, db: Session = Depends(get_db)):
    """Create a new safety plan."""
    return SafetyPlanService.create(db, data)


@router_su.get("/plans", response_model=List[SafetyPlanResponse])
def list_plans(db: Session = Depends(get_db)):
    """List all safety plans."""
    return SafetyPlanService.list_all(db)


@router_su.get("/plans/{plan_id}", response_model=SafetyPlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get a specific safety plan."""
    plan = SafetyPlanService.get(db, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


@router_su.put("/plans/{plan_id}", response_model=SafetyPlanResponse)
def update_plan(plan_id: int, data: SafetyPlanUpdate, db: Session = Depends(get_db)):
    """Update a safety plan."""
    plan = SafetyPlanService.update(db, plan_id, data)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


@router_su.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    """Delete a safety plan."""
    if not SafetyPlanService.delete(db, plan_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")


# Safety Event Logs
@router_su.post("/events", response_model=SafetyEventLogResponse, status_code=status.HTTP_201_CREATED)
def create_event_log(data: SafetyEventLogCreate, db: Session = Depends(get_db)):
    """Create a new safety event log."""
    return SafetyEventLogService.create(db, data)


@router_su.get("/events/{log_id}", response_model=SafetyEventLogResponse)
def get_event_log(log_id: int, db: Session = Depends(get_db)):
    """Get a specific event log."""
    log = SafetyEventLogService.get(db, log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event log not found")
    return log


@router_su.get("/categories/{category_id}/events", response_model=List[SafetyEventLogResponse])
def list_category_events(category_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List event logs for a category."""
    return SafetyEventLogService.list_by_category(db, category_id, skip, limit)


# ============================================================================
# PACK SV: Empire Growth Navigator Router
# ============================================================================

router_sv = APIRouter(prefix="/api/v1/empire", tags=["Empire Growth"])


# Empire Goals
@router_sv.post("/goals", response_model=EmpireGoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(data: EmpireGoalCreate, db: Session = Depends(get_db)):
    """Create a new empire goal."""
    return EmpireGoalService.create(db, data)


@router_sv.get("/goals", response_model=List[EmpireGoalResponse])
def list_goals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all empire goals."""
    return EmpireGoalService.list_all(db, skip, limit)


@router_sv.get("/goals/{goal_id}", response_model=EmpireGoalResponse)
def get_goal(goal_id: int, db: Session = Depends(get_db)):
    """Get a specific empire goal."""
    goal = EmpireGoalService.get(db, goal_id)
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal


@router_sv.get("/goals/status/{status}", response_model=List[EmpireGoalResponse])
def list_goals_by_status(status: str, db: Session = Depends(get_db)):
    """List goals by status."""
    return EmpireGoalService.list_by_status(db, status)


@router_sv.put("/goals/{goal_id}", response_model=EmpireGoalResponse)
def update_goal(goal_id: int, data: EmpireGoalUpdate, db: Session = Depends(get_db)):
    """Update an empire goal."""
    goal = EmpireGoalService.update(db, goal_id, data)
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal


@router_sv.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    """Delete an empire goal."""
    if not EmpireGoalService.delete(db, goal_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")


# Goal Milestones
@router_sv.post("/milestones", response_model=GoalMilestoneResponse, status_code=status.HTTP_201_CREATED)
def create_milestone(data: GoalMilestoneCreate, db: Session = Depends(get_db)):
    """Create a new goal milestone."""
    return GoalMilestoneService.create(db, data)


@router_sv.get("/milestones/{milestone_id}", response_model=GoalMilestoneResponse)
def get_milestone(milestone_id: int, db: Session = Depends(get_db)):
    """Get a specific milestone."""
    milestone = GoalMilestoneService.get(db, milestone_id)
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")
    return milestone


@router_sv.get("/goals/{goal_id}/milestones", response_model=List[GoalMilestoneResponse])
def list_goal_milestones(goal_id: int, db: Session = Depends(get_db)):
    """List milestones for a goal."""
    return GoalMilestoneService.list_by_goal(db, goal_id)


@router_sv.put("/milestones/{milestone_id}", response_model=GoalMilestoneResponse)
def update_milestone(milestone_id: int, data: GoalMilestoneUpdate, db: Session = Depends(get_db)):
    """Update a goal milestone."""
    milestone = GoalMilestoneService.update(db, milestone_id, data)
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")
    return milestone


@router_sv.delete("/milestones/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_milestone(milestone_id: int, db: Session = Depends(get_db)):
    """Delete a milestone."""
    if not GoalMilestoneService.delete(db, milestone_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")


# Action Steps
@router_sv.post("/steps", response_model=ActionStepResponse, status_code=status.HTTP_201_CREATED)
def create_step(data: ActionStepCreate, db: Session = Depends(get_db)):
    """Create a new action step."""
    return ActionStepService.create(db, data)


@router_sv.get("/steps/{step_id}", response_model=ActionStepResponse)
def get_step(step_id: int, db: Session = Depends(get_db)):
    """Get a specific action step."""
    step = ActionStepService.get(db, step_id)
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action step not found")
    return step


@router_sv.get("/milestones/{milestone_id}/steps", response_model=List[ActionStepResponse])
def list_milestone_steps(milestone_id: int, db: Session = Depends(get_db)):
    """List action steps for a milestone."""
    return ActionStepService.list_by_milestone(db, milestone_id)


@router_sv.put("/steps/{step_id}", response_model=ActionStepResponse)
def update_step(step_id: int, data: ActionStepUpdate, db: Session = Depends(get_db)):
    """Update an action step."""
    step = ActionStepService.update(db, step_id, data)
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action step not found")
    return step


@router_sv.delete("/steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_step(step_id: int, db: Session = Depends(get_db)):
    """Delete an action step."""
    if not ActionStepService.delete(db, step_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action step not found")
