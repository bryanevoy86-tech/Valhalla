"""
Service functions for PACK ST, SU, SV

Handles database operations and business logic.
"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from app.models.pack_st import FinancialIndicator, FinancialStressEvent, FinancialStressSummary
from app.models.pack_su import SafetyCategory, SafetyChecklist, SafetyPlan, SafetyEventLog
from app.models.pack_sv import EmpireGoal, GoalMilestone, ActionStep
from app.schemas.pack_st_su_sv import (
    FinancialIndicatorCreate, FinancialIndicatorUpdate,
    FinancialStressEventCreate, FinancialStressEventUpdate,
    FinancialStressSummaryCreate, FinancialStressSummaryUpdate,
    SafetyCategoryCreate, SafetyCategoryUpdate,
    SafetyChecklistCreate, SafetyChecklistUpdate,
    SafetyPlanCreate, SafetyPlanUpdate,
    SafetyEventLogCreate,
    EmpireGoalCreate, EmpireGoalUpdate,
    GoalMilestoneCreate, GoalMilestoneUpdate,
    ActionStepCreate, ActionStepUpdate
)
from app.util.id_gen import generate_id


# ============================================================================
# PACK ST: Financial Stress Early Warning Engine Services
# ============================================================================

class FinancialIndicatorService:
    """Financial indicator management."""

    @staticmethod
    def create(db: Session, data: FinancialIndicatorCreate) -> FinancialIndicator:
        """Create a new financial indicator."""
        indicator = FinancialIndicator(
            indicator_id=generate_id("finind"),
            name=data.name,
            category=data.category,
            threshold_type=data.threshold_type,
            threshold_value=data.threshold_value,
            notes=data.notes
        )
        db.add(indicator)
        db.commit()
        db.refresh(indicator)
        return indicator

    @staticmethod
    def get(db: Session, indicator_id: int) -> Optional[FinancialIndicator]:
        """Get indicator by ID."""
        return db.query(FinancialIndicator).filter(FinancialIndicator.id == indicator_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[FinancialIndicator]:
        """List all indicators."""
        return db.query(FinancialIndicator).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, indicator_id: int, data: FinancialIndicatorUpdate) -> Optional[FinancialIndicator]:
        """Update a financial indicator."""
        indicator = db.query(FinancialIndicator).filter(FinancialIndicator.id == indicator_id).first()
        if not indicator:
            return None
        
        if data.name is not None:
            indicator.name = data.name
        if data.category is not None:
            indicator.category = data.category
        if data.threshold_type is not None:
            indicator.threshold_type = data.threshold_type
        if data.threshold_value is not None:
            indicator.threshold_value = data.threshold_value
        if data.notes is not None:
            indicator.notes = data.notes
        indicator.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(indicator)
        return indicator

    @staticmethod
    def delete(db: Session, indicator_id: int) -> bool:
        """Delete an indicator."""
        indicator = db.query(FinancialIndicator).filter(FinancialIndicator.id == indicator_id).first()
        if not indicator:
            return False
        db.delete(indicator)
        db.commit()
        return True


class FinancialStressEventService:
    """Financial stress event management."""

    @staticmethod
    def create(db: Session, data: FinancialStressEventCreate) -> FinancialStressEvent:
        """Create a new stress event."""
        event = FinancialStressEvent(
            event_id=generate_id("stressev"),
            indicator_id=data.indicator_id,
            date=data.date,
            value_at_trigger=data.value_at_trigger,
            description=data.description,
            resolved=data.resolved or False,
            notes=data.notes
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def get(db: Session, event_id: int) -> Optional[FinancialStressEvent]:
        """Get event by ID."""
        return db.query(FinancialStressEvent).filter(FinancialStressEvent.id == event_id).first()

    @staticmethod
    def list_by_indicator(db: Session, indicator_id: int, skip: int = 0, limit: int = 100) -> List[FinancialStressEvent]:
        """List events for an indicator."""
        return db.query(FinancialStressEvent)\
            .filter(FinancialStressEvent.indicator_id == indicator_id)\
            .order_by(FinancialStressEvent.date.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def update(db: Session, event_id: int, data: FinancialStressEventUpdate) -> Optional[FinancialStressEvent]:
        """Update a stress event."""
        event = db.query(FinancialStressEvent).filter(FinancialStressEvent.id == event_id).first()
        if not event:
            return None
        
        if data.resolved is not None:
            event.resolved = data.resolved
        if data.notes is not None:
            event.notes = data.notes
        event.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(event)
        return event


class FinancialStressSummaryService:
    """Financial stress summary management."""

    @staticmethod
    def create(db: Session, data: FinancialStressSummaryCreate) -> FinancialStressSummary:
        """Create a new summary."""
        summary = FinancialStressSummary(
            summary_id=generate_id("finsum"),
            month=data.month,
            triggered_indicators=data.triggered_indicators,
            patterns=data.patterns,
            recommendations_to_self=data.recommendations_to_self,
            notes=data.notes
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
        return summary

    @staticmethod
    def get(db: Session, summary_id: int) -> Optional[FinancialStressSummary]:
        """Get summary by ID."""
        return db.query(FinancialStressSummary).filter(FinancialStressSummary.id == summary_id).first()

    @staticmethod
    def get_by_month(db: Session, month: str) -> Optional[FinancialStressSummary]:
        """Get summary for a specific month."""
        return db.query(FinancialStressSummary).filter(FinancialStressSummary.month == month).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[FinancialStressSummary]:
        """List all summaries."""
        return db.query(FinancialStressSummary).order_by(FinancialStressSummary.month.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, summary_id: int, data: FinancialStressSummaryUpdate) -> Optional[FinancialStressSummary]:
        """Update a summary."""
        summary = db.query(FinancialStressSummary).filter(FinancialStressSummary.id == summary_id).first()
        if not summary:
            return None
        
        if data.triggered_indicators is not None:
            summary.triggered_indicators = data.triggered_indicators
        if data.patterns is not None:
            summary.patterns = data.patterns
        if data.recommendations_to_self is not None:
            summary.recommendations_to_self = data.recommendations_to_self
        if data.notes is not None:
            summary.notes = data.notes
        summary.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(summary)
        return summary


# ============================================================================
# PACK SU: Personal Safety & Risk Mitigation Planner Services
# ============================================================================

class SafetyCategoryService:
    """Safety category management."""

    @staticmethod
    def create(db: Session, data: SafetyCategoryCreate) -> SafetyCategory:
        """Create a new safety category."""
        category = SafetyCategory(
            category_id=generate_id("safecat"),
            name=data.name,
            description=data.description
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def get(db: Session, category_id: int) -> Optional[SafetyCategory]:
        """Get category by ID."""
        return db.query(SafetyCategory).filter(SafetyCategory.id == category_id).first()

    @staticmethod
    def list_all(db: Session) -> List[SafetyCategory]:
        """List all categories."""
        return db.query(SafetyCategory).all()

    @staticmethod
    def update(db: Session, category_id: int, data: SafetyCategoryUpdate) -> Optional[SafetyCategory]:
        """Update a category."""
        category = db.query(SafetyCategory).filter(SafetyCategory.id == category_id).first()
        if not category:
            return None
        
        if data.name is not None:
            category.name = data.name
        if data.description is not None:
            category.description = data.description
        category.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def delete(db: Session, category_id: int) -> bool:
        """Delete a category."""
        category = db.query(SafetyCategory).filter(SafetyCategory.id == category_id).first()
        if not category:
            return False
        db.delete(category)
        db.commit()
        return True


class SafetyChecklistService:
    """Safety checklist management."""

    @staticmethod
    def create(db: Session, data: SafetyChecklistCreate) -> SafetyChecklist:
        """Create a new checklist item."""
        checklist = SafetyChecklist(
            checklist_id=generate_id("safechk"),
            category_id=data.category_id,
            item=data.item,
            frequency=data.frequency,
            notes=data.notes,
            status=data.status or "active"
        )
        db.add(checklist)
        db.commit()
        db.refresh(checklist)
        return checklist

    @staticmethod
    def get(db: Session, checklist_id: int) -> Optional[SafetyChecklist]:
        """Get checklist by ID."""
        return db.query(SafetyChecklist).filter(SafetyChecklist.id == checklist_id).first()

    @staticmethod
    def list_by_category(db: Session, category_id: int) -> List[SafetyChecklist]:
        """List checklists for a category."""
        return db.query(SafetyChecklist).filter(SafetyChecklist.category_id == category_id).all()

    @staticmethod
    def update(db: Session, checklist_id: int, data: SafetyChecklistUpdate) -> Optional[SafetyChecklist]:
        """Update a checklist item."""
        checklist = db.query(SafetyChecklist).filter(SafetyChecklist.id == checklist_id).first()
        if not checklist:
            return None
        
        if data.item is not None:
            checklist.item = data.item
        if data.frequency is not None:
            checklist.frequency = data.frequency
        if data.notes is not None:
            checklist.notes = data.notes
        if data.status is not None:
            checklist.status = data.status
        checklist.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(checklist)
        return checklist

    @staticmethod
    def delete(db: Session, checklist_id: int) -> bool:
        """Delete a checklist item."""
        checklist = db.query(SafetyChecklist).filter(SafetyChecklist.id == checklist_id).first()
        if not checklist:
            return False
        db.delete(checklist)
        db.commit()
        return True


class SafetyPlanService:
    """Safety plan management."""

    @staticmethod
    def create(db: Session, data: SafetyPlanCreate) -> SafetyPlan:
        """Create a new safety plan."""
        plan = SafetyPlan(
            plan_id=generate_id("safeplan"),
            situation=data.situation,
            steps=[s.model_dump() for s in data.steps] if data.steps else None,
            notes=data.notes
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def get(db: Session, plan_id: int) -> Optional[SafetyPlan]:
        """Get plan by ID."""
        return db.query(SafetyPlan).filter(SafetyPlan.id == plan_id).first()

    @staticmethod
    def list_all(db: Session) -> List[SafetyPlan]:
        """List all plans."""
        return db.query(SafetyPlan).all()

    @staticmethod
    def update(db: Session, plan_id: int, data: SafetyPlanUpdate) -> Optional[SafetyPlan]:
        """Update a safety plan."""
        plan = db.query(SafetyPlan).filter(SafetyPlan.id == plan_id).first()
        if not plan:
            return None
        
        if data.situation is not None:
            plan.situation = data.situation
        if data.steps is not None:
            plan.steps = [s.model_dump() for s in data.steps]
        if data.notes is not None:
            plan.notes = data.notes
        plan.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def delete(db: Session, plan_id: int) -> bool:
        """Delete a safety plan."""
        plan = db.query(SafetyPlan).filter(SafetyPlan.id == plan_id).first()
        if not plan:
            return False
        db.delete(plan)
        db.commit()
        return True


class SafetyEventLogService:
    """Safety event log management."""

    @staticmethod
    def create(db: Session, data: SafetyEventLogCreate) -> SafetyEventLog:
        """Create a new event log."""
        log = SafetyEventLog(
            log_id=generate_id("safelog"),
            date=data.date,
            category_id=data.category_id,
            event=data.event,
            resolution_notes=data.resolution_notes
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get(db: Session, log_id: int) -> Optional[SafetyEventLog]:
        """Get log by ID."""
        return db.query(SafetyEventLog).filter(SafetyEventLog.id == log_id).first()

    @staticmethod
    def list_by_category(db: Session, category_id: int, skip: int = 0, limit: int = 100) -> List[SafetyEventLog]:
        """List logs for a category."""
        return db.query(SafetyEventLog)\
            .filter(SafetyEventLog.category_id == category_id)\
            .order_by(SafetyEventLog.date.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()


# ============================================================================
# PACK SV: Empire Growth Navigator Services
# ============================================================================

class EmpireGoalService:
    """Empire goal management."""

    @staticmethod
    def create(db: Session, data: EmpireGoalCreate) -> EmpireGoal:
        """Create a new empire goal."""
        goal = EmpireGoal(
            goal_id=generate_id("empgoal"),
            name=data.name,
            category=data.category,
            description=data.description,
            timeframe=data.timeframe,
            status=data.status or "not_started",
            notes=data.notes
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return goal

    @staticmethod
    def get(db: Session, goal_id: int) -> Optional[EmpireGoal]:
        """Get goal by ID."""
        return db.query(EmpireGoal).filter(EmpireGoal.id == goal_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[EmpireGoal]:
        """List all goals."""
        return db.query(EmpireGoal).offset(skip).limit(limit).all()

    @staticmethod
    def list_by_status(db: Session, status: str) -> List[EmpireGoal]:
        """List goals by status."""
        return db.query(EmpireGoal).filter(EmpireGoal.status == status).all()

    @staticmethod
    def update(db: Session, goal_id: int, data: EmpireGoalUpdate) -> Optional[EmpireGoal]:
        """Update a goal."""
        goal = db.query(EmpireGoal).filter(EmpireGoal.id == goal_id).first()
        if not goal:
            return None
        
        if data.name is not None:
            goal.name = data.name
        if data.category is not None:
            goal.category = data.category
        if data.description is not None:
            goal.description = data.description
        if data.timeframe is not None:
            goal.timeframe = data.timeframe
        if data.status is not None:
            goal.status = data.status
        if data.notes is not None:
            goal.notes = data.notes
        goal.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(goal)
        return goal

    @staticmethod
    def delete(db: Session, goal_id: int) -> bool:
        """Delete a goal."""
        goal = db.query(EmpireGoal).filter(EmpireGoal.id == goal_id).first()
        if not goal:
            return False
        db.delete(goal)
        db.commit()
        return True


class GoalMilestoneService:
    """Goal milestone management."""

    @staticmethod
    def create(db: Session, data: GoalMilestoneCreate) -> GoalMilestone:
        """Create a new milestone."""
        milestone = GoalMilestone(
            milestone_id=generate_id("miles"),
            goal_id=data.goal_id,
            description=data.description,
            due_date=data.due_date,
            progress=data.progress or 0.0,
            notes=data.notes
        )
        db.add(milestone)
        db.commit()
        db.refresh(milestone)
        return milestone

    @staticmethod
    def get(db: Session, milestone_id: int) -> Optional[GoalMilestone]:
        """Get milestone by ID."""
        return db.query(GoalMilestone).filter(GoalMilestone.id == milestone_id).first()

    @staticmethod
    def list_by_goal(db: Session, goal_id: int) -> List[GoalMilestone]:
        """List milestones for a goal."""
        return db.query(GoalMilestone).filter(GoalMilestone.goal_id == goal_id).all()

    @staticmethod
    def update(db: Session, milestone_id: int, data: GoalMilestoneUpdate) -> Optional[GoalMilestone]:
        """Update a milestone."""
        milestone = db.query(GoalMilestone).filter(GoalMilestone.id == milestone_id).first()
        if not milestone:
            return None
        
        if data.description is not None:
            milestone.description = data.description
        if data.due_date is not None:
            milestone.due_date = data.due_date
        if data.progress is not None:
            milestone.progress = data.progress
        if data.notes is not None:
            milestone.notes = data.notes
        milestone.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(milestone)
        return milestone

    @staticmethod
    def delete(db: Session, milestone_id: int) -> bool:
        """Delete a milestone."""
        milestone = db.query(GoalMilestone).filter(GoalMilestone.id == milestone_id).first()
        if not milestone:
            return False
        db.delete(milestone)
        db.commit()
        return True


class ActionStepService:
    """Action step management."""

    @staticmethod
    def create(db: Session, data: ActionStepCreate) -> ActionStep:
        """Create a new action step."""
        step = ActionStep(
            step_id=generate_id("step"),
            milestone_id=data.milestone_id,
            description=data.description,
            priority=data.priority or 1,
            status=data.status or "pending",
            notes=data.notes
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        return step

    @staticmethod
    def get(db: Session, step_id: int) -> Optional[ActionStep]:
        """Get action step by ID."""
        return db.query(ActionStep).filter(ActionStep.id == step_id).first()

    @staticmethod
    def list_by_milestone(db: Session, milestone_id: int) -> List[ActionStep]:
        """List steps for a milestone."""
        return db.query(ActionStep)\
            .filter(ActionStep.milestone_id == milestone_id)\
            .order_by(ActionStep.priority)\
            .all()

    @staticmethod
    def update(db: Session, step_id: int, data: ActionStepUpdate) -> Optional[ActionStep]:
        """Update an action step."""
        step = db.query(ActionStep).filter(ActionStep.id == step_id).first()
        if not step:
            return None
        
        if data.description is not None:
            step.description = data.description
        if data.priority is not None:
            step.priority = data.priority
        if data.status is not None:
            step.status = data.status
        if data.notes is not None:
            step.notes = data.notes
        step.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(step)
        return step

    @staticmethod
    def delete(db: Session, step_id: int) -> bool:
        """Delete an action step."""
        step = db.query(ActionStep).filter(ActionStep.id == step_id).first()
        if not step:
            return False
        db.delete(step)
        db.commit()
        return True
