"""
Test suite for PACK ST, SU, SV

Comprehensive tests for financial stress, personal safety, and empire growth.
"""

import pytest
from datetime import date, datetime
from sqlalchemy.orm import Session

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
from app.services.pack_st_su_sv import (
    FinancialIndicatorService, FinancialStressEventService, FinancialStressSummaryService,
    SafetyCategoryService, SafetyChecklistService, SafetyPlanService, SafetyEventLogService,
    EmpireGoalService, GoalMilestoneService, ActionStepService
)


# =============================================================================
# PACK ST: Financial Stress Early Warning Engine Tests
# =============================================================================

class TestFinancialIndicator:
    """Test FinancialIndicator model and service."""

    def test_create_indicator(self, db: Session):
        """Test creating a financial indicator."""
        data = FinancialIndicatorCreate(
            name="Monthly Income",
            category="income",
            threshold_type="below",
            threshold_value=3000.0,
            notes="Alert if income drops below $3000"
        )
        indicator = FinancialIndicatorService.create(db, data)
        
        assert indicator.id is not None
        assert indicator.indicator_id.startswith("finind-")
        assert indicator.name == "Monthly Income"
        assert indicator.category == "income"
        assert indicator.threshold_type == "below"
        assert indicator.threshold_value == 3000.0
        db.delete(indicator)
        db.commit()

    def test_get_indicator(self, db: Session):
        """Test retrieving a financial indicator."""
        data = FinancialIndicatorCreate(
            name="Savings Rate",
            category="savings",
            threshold_type="below",
            threshold_value=10.0
        )
        created = FinancialIndicatorService.create(db, data)
        retrieved = FinancialIndicatorService.get(db, created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Savings Rate"
        db.delete(retrieved)
        db.commit()

    def test_list_indicators(self, db: Session):
        """Test listing all financial indicators."""
        data1 = FinancialIndicatorCreate(
            name="Indicator 1",
            category="income",
            threshold_type="below",
            threshold_value=1000.0
        )
        data2 = FinancialIndicatorCreate(
            name="Indicator 2",
            category="expenses",
            threshold_type="above",
            threshold_value=5000.0
        )
        ind1 = FinancialIndicatorService.create(db, data1)
        ind2 = FinancialIndicatorService.create(db, data2)
        
        indicators = FinancialIndicatorService.list_all(db, 0, 100)
        assert len(indicators) >= 2
        
        db.delete(ind1)
        db.delete(ind2)
        db.commit()

    def test_update_indicator(self, db: Session):
        """Test updating a financial indicator."""
        data = FinancialIndicatorCreate(
            name="Original Name",
            category="income",
            threshold_type="below",
            threshold_value=2000.0
        )
        created = FinancialIndicatorService.create(db, data)
        
        update_data = FinancialIndicatorUpdate(
            name="Updated Name",
            threshold_value=2500.0
        )
        updated = FinancialIndicatorService.update(db, created.id, update_data)
        
        assert updated.name == "Updated Name"
        assert updated.threshold_value == 2500.0
        db.delete(updated)
        db.commit()

    def test_delete_indicator(self, db: Session):
        """Test deleting a financial indicator."""
        data = FinancialIndicatorCreate(
            name="To Delete",
            category="income",
            threshold_type="below",
            threshold_value=1500.0
        )
        created = FinancialIndicatorService.create(db, data)
        
        success = FinancialIndicatorService.delete(db, created.id)
        assert success is True
        
        retrieved = FinancialIndicatorService.get(db, created.id)
        assert retrieved is None


class TestFinancialStressEvent:
    """Test FinancialStressEvent model and service."""

    def test_create_stress_event(self, db: Session):
        """Test creating a stress event."""
        indicator_data = FinancialIndicatorCreate(
            name="Test Income",
            category="income",
            threshold_type="below",
            threshold_value=3000.0
        )
        indicator = FinancialIndicatorService.create(db, indicator_data)
        
        event_data = FinancialStressEventCreate(
            indicator_id=indicator.id,
            date=date.today(),
            value_at_trigger=2500.0,
            description="Monthly income below threshold",
            resolved=False
        )
        event = FinancialStressEventService.create(db, event_data)
        
        assert event.id is not None
        assert event.stress_event_id.startswith("stressev-")
        assert event.value_at_trigger == 2500.0
        
        db.delete(event)
        db.delete(indicator)
        db.commit()

    def test_get_stress_event(self, db: Session):
        """Test retrieving a stress event."""
        indicator_data = FinancialIndicatorCreate(
            name="Test Indicator",
            category="savings",
            threshold_type="below",
            threshold_value=5000.0
        )
        indicator = FinancialIndicatorService.create(db, indicator_data)
        
        event_data = FinancialStressEventCreate(
            indicator_id=indicator.id,
            date=date.today(),
            value_at_trigger=4000.0,
            description="Savings below threshold"
        )
        created = FinancialStressEventService.create(db, event_data)
        retrieved = FinancialStressEventService.get(db, created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        
        db.delete(retrieved)
        db.delete(indicator)
        db.commit()

    def test_list_events_by_indicator(self, db: Session):
        """Test listing events for an indicator."""
        indicator_data = FinancialIndicatorCreate(
            name="Test Indicator",
            category="income",
            threshold_type="below",
            threshold_value=2000.0
        )
        indicator = FinancialIndicatorService.create(db, indicator_data)
        
        event_data1 = FinancialStressEventCreate(
            indicator_id=indicator.id,
            date=date.today(),
            value_at_trigger=1800.0,
            description="Event 1"
        )
        event_data2 = FinancialStressEventCreate(
            indicator_id=indicator.id,
            date=date.today(),
            value_at_trigger=1900.0,
            description="Event 2"
        )
        event1 = FinancialStressEventService.create(db, event_data1)
        event2 = FinancialStressEventService.create(db, event_data2)
        
        events = FinancialStressEventService.list_by_indicator(db, indicator.id, 0, 100)
        assert len(events) >= 2
        
        db.delete(event1)
        db.delete(event2)
        db.delete(indicator)
        db.commit()

    def test_update_event_resolved(self, db: Session):
        """Test updating event resolved status."""
        indicator_data = FinancialIndicatorCreate(
            name="Test",
            category="income",
            threshold_type="below",
            threshold_value=1000.0
        )
        indicator = FinancialIndicatorService.create(db, indicator_data)
        
        event_data = FinancialStressEventCreate(
            indicator_id=indicator.id,
            date=date.today(),
            value_at_trigger=900.0,
            description="Test event",
            resolved=False
        )
        created = FinancialStressEventService.create(db, event_data)
        
        update_data = FinancialStressEventUpdate(resolved=True)
        updated = FinancialStressEventService.update(db, created.id, update_data)
        
        assert updated.resolved is True
        
        db.delete(updated)
        db.delete(indicator)
        db.commit()


class TestFinancialStressSummary:
    """Test FinancialStressSummary model and service."""

    def test_create_summary(self, db: Session):
        """Test creating a financial stress summary."""
        data = FinancialStressSummaryCreate(
            month="2024-01",
            triggered_indicators=["finind-001", "finind-002"],
            patterns=["recurring_at_month_start", "increasing_severity"],
            recommendations_to_self=["Review discretionary spending", "Track daily expenses"]
        )
        summary = FinancialStressSummaryService.create(db, data)
        
        assert summary.id is not None
        assert summary.financial_summary_id.startswith("finsum-")
        assert summary.month == "2024-01"
        assert len(summary.triggered_indicators) == 2
        
        db.delete(summary)
        db.commit()

    def test_get_summary_by_month(self, db: Session):
        """Test retrieving summary by month."""
        data = FinancialStressSummaryCreate(
            month="2024-02",
            triggered_indicators=["finind-001"],
            patterns=["recurring"],
            recommendations_to_self=["Save more"]
        )
        created = FinancialStressSummaryService.create(db, data)
        retrieved = FinancialStressSummaryService.get_by_month(db, "2024-02")
        
        assert retrieved is not None
        assert retrieved.month == "2024-02"
        
        db.delete(retrieved)
        db.commit()


# =============================================================================
# PACK SU: Personal Safety & Risk Mitigation Planner Tests
# =============================================================================

class TestSafetyCategory:
    """Test SafetyCategory model and service."""

    def test_create_category(self, db: Session):
        """Test creating a safety category."""
        data = SafetyCategoryCreate(
            name="Home Security",
            description="Routines for securing the home"
        )
        category = SafetyCategoryService.create(db, data)
        
        assert category.id is not None
        assert category.safety_category_id.startswith("safecat-")
        assert category.name == "Home Security"
        
        db.delete(category)
        db.commit()

    def test_list_categories(self, db: Session):
        """Test listing all safety categories."""
        data1 = SafetyCategoryCreate(
            name="Category 1",
            description="Description 1"
        )
        data2 = SafetyCategoryCreate(
            name="Category 2",
            description="Description 2"
        )
        cat1 = SafetyCategoryService.create(db, data1)
        cat2 = SafetyCategoryService.create(db, data2)
        
        categories = SafetyCategoryService.list_all(db)
        assert len(categories) >= 2
        
        db.delete(cat1)
        db.delete(cat2)
        db.commit()

    def test_update_category(self, db: Session):
        """Test updating a safety category."""
        data = SafetyCategoryCreate(
            name="Original",
            description="Original description"
        )
        created = SafetyCategoryService.create(db, data)
        
        update_data = SafetyCategoryUpdate(
            name="Updated",
            description="Updated description"
        )
        updated = SafetyCategoryService.update(db, created.id, update_data)
        
        assert updated.name == "Updated"
        
        db.delete(updated)
        db.commit()


class TestSafetyChecklist:
    """Test SafetyChecklist model and service."""

    def test_create_checklist(self, db: Session):
        """Test creating a safety checklist item."""
        category_data = SafetyCategoryCreate(
            name="Test Category",
            description="Test"
        )
        category = SafetyCategoryService.create(db, category_data)
        
        checklist_data = SafetyChecklistCreate(
            category_id=category.id,
            item="Lock all doors",
            frequency="daily",
            status="active"
        )
        checklist = SafetyChecklistService.create(db, checklist_data)
        
        assert checklist.id is not None
        assert checklist.safety_checklist_id.startswith("safechk-")
        assert checklist.item == "Lock all doors"
        
        db.delete(checklist)
        db.delete(category)
        db.commit()

    def test_list_checklists_by_category(self, db: Session):
        """Test listing checklists for a category."""
        category_data = SafetyCategoryCreate(
            name="Test",
            description="Test"
        )
        category = SafetyCategoryService.create(db, category_data)
        
        check_data1 = SafetyChecklistCreate(
            category_id=category.id,
            item="Item 1",
            frequency="daily",
            status="active"
        )
        check_data2 = SafetyChecklistCreate(
            category_id=category.id,
            item="Item 2",
            frequency="weekly",
            status="active"
        )
        check1 = SafetyChecklistService.create(db, check_data1)
        check2 = SafetyChecklistService.create(db, check_data2)
        
        checklists = SafetyChecklistService.list_by_category(db, category.id)
        assert len(checklists) >= 2
        
        db.delete(check1)
        db.delete(check2)
        db.delete(category)
        db.commit()


class TestSafetyPlan:
    """Test SafetyPlan model and service."""

    def test_create_plan(self, db: Session):
        """Test creating a safety plan."""
        data = SafetyPlanCreate(
            situation="Emergency evacuation",
            steps=[
                {"step": "Gather documents", "order": 1},
                {"step": "Move to safe location", "order": 2},
                {"step": "Contact family", "order": 3}
            ]
        )
        plan = SafetyPlanService.create(db, data)
        
        assert plan.id is not None
        assert plan.safety_plan_id.startswith("safeplan-")
        assert plan.situation == "Emergency evacuation"
        assert len(plan.steps) == 3
        
        db.delete(plan)
        db.commit()

    def test_list_plans(self, db: Session):
        """Test listing all safety plans."""
        data1 = SafetyPlanCreate(
            situation="Situation 1",
            steps=[{"step": "Step 1", "order": 1}]
        )
        data2 = SafetyPlanCreate(
            situation="Situation 2",
            steps=[{"step": "Step 2", "order": 1}]
        )
        plan1 = SafetyPlanService.create(db, data1)
        plan2 = SafetyPlanService.create(db, data2)
        
        plans = SafetyPlanService.list_all(db)
        assert len(plans) >= 2
        
        db.delete(plan1)
        db.delete(plan2)
        db.commit()


class TestSafetyEventLog:
    """Test SafetyEventLog model and service."""

    def test_create_event_log(self, db: Session):
        """Test creating a safety event log."""
        category_data = SafetyCategoryCreate(
            name="Test",
            description="Test"
        )
        category = SafetyCategoryService.create(db, category_data)
        
        log_data = SafetyEventLogCreate(
            date=date.today(),
            category_id=category.id,
            event="Security breach detected"
        )
        log = SafetyEventLogService.create(db, log_data)
        
        assert log.id is not None
        assert log.safety_event_log_id.startswith("safelog-")
        
        db.delete(log)
        db.delete(category)
        db.commit()

    def test_list_events_by_category(self, db: Session):
        """Test listing events for a category."""
        category_data = SafetyCategoryCreate(
            name="Test",
            description="Test"
        )
        category = SafetyCategoryService.create(db, category_data)
        
        log_data1 = SafetyEventLogCreate(
            date=date.today(),
            category_id=category.id,
            event="Event 1"
        )
        log_data2 = SafetyEventLogCreate(
            date=date.today(),
            category_id=category.id,
            event="Event 2"
        )
        log1 = SafetyEventLogService.create(db, log_data1)
        log2 = SafetyEventLogService.create(db, log_data2)
        
        events = SafetyEventLogService.list_by_category(db, category.id, 0, 100)
        assert len(events) >= 2
        
        db.delete(log1)
        db.delete(log2)
        db.delete(category)
        db.commit()


# =============================================================================
# PACK SV: Empire Growth Navigator Tests
# =============================================================================

class TestEmpireGoal:
    """Test EmpireGoal model and service."""

    def test_create_goal(self, db: Session):
        """Test creating an empire goal."""
        data = EmpireGoalCreate(
            name="Achieve Financial Independence",
            category="finance",
            description="Build wealth to support lifestyle",
            timeframe="long_term",
            status="in_progress"
        )
        goal = EmpireGoalService.create(db, data)
        
        assert goal.id is not None
        assert goal.empire_goal_id.startswith("empgoal-")
        assert goal.name == "Achieve Financial Independence"
        
        db.delete(goal)
        db.commit()

    def test_list_goals(self, db: Session):
        """Test listing all empire goals."""
        data1 = EmpireGoalCreate(
            name="Goal 1",
            category="finance",
            description="Desc 1",
            timeframe="short_term",
            status="not_started"
        )
        data2 = EmpireGoalCreate(
            name="Goal 2",
            category="business",
            description="Desc 2",
            timeframe="mid_term",
            status="in_progress"
        )
        goal1 = EmpireGoalService.create(db, data1)
        goal2 = EmpireGoalService.create(db, data2)
        
        goals = EmpireGoalService.list_all(db, 0, 100)
        assert len(goals) >= 2
        
        db.delete(goal1)
        db.delete(goal2)
        db.commit()

    def test_list_goals_by_status(self, db: Session):
        """Test listing goals by status."""
        data = EmpireGoalCreate(
            name="Test Goal",
            category="finance",
            description="Test",
            timeframe="short_term",
            status="completed"
        )
        goal = EmpireGoalService.create(db, data)
        
        goals = EmpireGoalService.list_by_status(db, "completed")
        assert len(goals) >= 1
        assert any(g.id == goal.id for g in goals)
        
        db.delete(goal)
        db.commit()

    def test_update_goal(self, db: Session):
        """Test updating an empire goal."""
        data = EmpireGoalCreate(
            name="Original",
            category="finance",
            description="Original description",
            timeframe="short_term",
            status="not_started"
        )
        created = EmpireGoalService.create(db, data)
        
        update_data = EmpireGoalUpdate(
            status="in_progress",
            description="Updated description"
        )
        updated = EmpireGoalService.update(db, created.id, update_data)
        
        assert updated.status == "in_progress"
        assert updated.description == "Updated description"
        
        db.delete(updated)
        db.commit()


class TestGoalMilestone:
    """Test GoalMilestone model and service."""

    def test_create_milestone(self, db: Session):
        """Test creating a goal milestone."""
        goal_data = EmpireGoalCreate(
            name="Test Goal",
            category="finance",
            description="Test",
            timeframe="long_term",
            status="not_started"
        )
        goal = EmpireGoalService.create(db, goal_data)
        
        milestone_data = GoalMilestoneCreate(
            goal_id=goal.id,
            description="Save first $10k",
            due_date=date(2025, 12, 31),
            progress=0.5
        )
        milestone = GoalMilestoneService.create(db, milestone_data)
        
        assert milestone.id is not None
        assert milestone.milestone_id.startswith("miles-")
        assert milestone.progress == 0.5
        
        db.delete(milestone)
        db.delete(goal)
        db.commit()

    def test_list_milestones_by_goal(self, db: Session):
        """Test listing milestones for a goal."""
        goal_data = EmpireGoalCreate(
            name="Test",
            category="finance",
            description="Test",
            timeframe="long_term",
            status="not_started"
        )
        goal = EmpireGoalService.create(db, goal_data)
        
        mile_data1 = GoalMilestoneCreate(
            goal_id=goal.id,
            description="Milestone 1",
            progress=0.3
        )
        mile_data2 = GoalMilestoneCreate(
            goal_id=goal.id,
            description="Milestone 2",
            progress=0.7
        )
        mile1 = GoalMilestoneService.create(db, mile_data1)
        mile2 = GoalMilestoneService.create(db, mile_data2)
        
        milestones = GoalMilestoneService.list_by_goal(db, goal.id)
        assert len(milestones) >= 2
        
        db.delete(mile1)
        db.delete(mile2)
        db.delete(goal)
        db.commit()

    def test_update_milestone_progress(self, db: Session):
        """Test updating milestone progress."""
        goal_data = EmpireGoalCreate(
            name="Test",
            category="finance",
            description="Test",
            timeframe="long_term",
            status="not_started"
        )
        goal = EmpireGoalService.create(db, goal_data)
        
        mile_data = GoalMilestoneCreate(
            goal_id=goal.id,
            description="Test",
            progress=0.0
        )
        created = GoalMilestoneService.create(db, mile_data)
        
        update_data = GoalMilestoneUpdate(progress=0.8)
        updated = GoalMilestoneService.update(db, created.id, update_data)
        
        assert updated.progress == 0.8
        
        db.delete(updated)
        db.delete(goal)
        db.commit()


class TestActionStep:
    """Test ActionStep model and service."""

    def test_create_step(self, db: Session):
        """Test creating an action step."""
        goal_data = EmpireGoalCreate(
            name="Test",
            category="finance",
            description="Test",
            timeframe="long_term",
            status="not_started"
        )
        goal = EmpireGoalService.create(db, goal_data)
        
        mile_data = GoalMilestoneCreate(
            goal_id=goal.id,
            description="Test",
            progress=0.0
        )
        milestone = GoalMilestoneService.create(db, mile_data)
        
        step_data = ActionStepCreate(
            milestone_id=milestone.id,
            description="Save $500 this month",
            priority=1,
            status="pending"
        )
        step = ActionStepService.create(db, step_data)
        
        assert step.id is not None
        assert step.step_id.startswith("step-")
        assert step.priority == 1
        
        db.delete(step)
        db.delete(milestone)
        db.delete(goal)
        db.commit()

    def test_list_steps_by_milestone(self, db: Session):
        """Test listing steps for a milestone."""
        goal_data = EmpireGoalCreate(
            name="Test",
            category="finance",
            description="Test",
            timeframe="long_term",
            status="not_started"
        )
        goal = EmpireGoalService.create(db, goal_data)
        
        mile_data = GoalMilestoneCreate(
            goal_id=goal.id,
            description="Test",
            progress=0.0
        )
        milestone = GoalMilestoneService.create(db, mile_data)
        
        step_data1 = ActionStepCreate(
            milestone_id=milestone.id,
            description="Step 1",
            priority=1,
            status="pending"
        )
        step_data2 = ActionStepCreate(
            milestone_id=milestone.id,
            description="Step 2",
            priority=2,
            status="pending"
        )
        step1 = ActionStepService.create(db, step_data1)
        step2 = ActionStepService.create(db, step_data2)
        
        steps = ActionStepService.list_by_milestone(db, milestone.id)
        assert len(steps) >= 2
        
        db.delete(step1)
        db.delete(step2)
        db.delete(milestone)
        db.delete(goal)
        db.commit()

    def test_update_step_status(self, db: Session):
        """Test updating step status."""
        goal_data = EmpireGoalCreate(
            name="Test",
            category="finance",
            description="Test",
            timeframe="long_term",
            status="not_started"
        )
        goal = EmpireGoalService.create(db, goal_data)
        
        mile_data = GoalMilestoneCreate(
            goal_id=goal.id,
            description="Test",
            progress=0.0
        )
        milestone = GoalMilestoneService.create(db, mile_data)
        
        step_data = ActionStepCreate(
            milestone_id=milestone.id,
            description="Test",
            priority=1,
            status="pending"
        )
        created = ActionStepService.create(db, step_data)
        
        update_data = ActionStepUpdate(status="done")
        updated = ActionStepService.update(db, created.id, update_data)
        
        assert updated.status == "done"
        
        db.delete(updated)
        db.delete(milestone)
        db.delete(goal)
        db.commit()
