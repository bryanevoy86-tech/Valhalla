"""PACK ST, SU, SV: Financial Stress, Personal Safety, Empire Growth

Revision ID: 0060_pack_st_su_sv
Revises: 0059_integrity_telemetry
Create Date: 2025-11-07

PACK ST - Financial Stress Early Warning Engine
  - FinancialIndicator: User-defined thresholds with category (income/expenses/cashflow/savings) and direction (above/below)
  - FinancialStressEvent: Event log when indicator triggers, with resolution tracking
  - FinancialStressSummary: Monthly aggregation with user patterns and recommendations

PACK SU - Personal Safety & Risk Mitigation Planner
  - SafetyCategory: Organization for safety routines (home, travel, digital, etc.)
  - SafetyChecklist: Individual items with frequency (daily/weekly/before_travel/as_needed)
  - SafetyPlan: Contingency plans for situations with ordered step lists
  - SafetyEventLog: Event logging with resolution notes (no diagnosis or advice)

PACK SV - Empire Growth Navigator
  - EmpireGoal: Top-level goals with category (finance/business/family/skills/real_estate/automation) and timeframe
  - GoalMilestone: Milestone within goal with progress tracking (0.0-1.0)
  - ActionStep: Individual steps within milestone with priority and status
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0060_pack_st_su_sv"
down_revision = "0059_integrity_telemetry"
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # PACK ST: Financial Stress Early Warning Engine
    # =========================================================================
    
    op.create_table(
        "financial_indicator",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("indicator_id", sa.String(32), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),  # income, expenses, cashflow, savings
        sa.Column("threshold_type", sa.String(16), nullable=False),  # above, below
        sa.Column("threshold_value", sa.Float, nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_financial_indicator_category", "financial_indicator", ["category"])
    op.create_index("ix_financial_indicator_indicator_id", "financial_indicator", ["indicator_id"], unique=True)
    
    op.create_table(
        "financial_stress_event",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("stress_event_id", sa.String(32), unique=True, nullable=False),
        sa.Column("indicator_id", sa.Integer, sa.ForeignKey("financial_indicator.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("value_at_trigger", sa.Float, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("resolved", sa.Boolean, server_default="false"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_financial_stress_event_indicator_id", "financial_stress_event", ["indicator_id"])
    op.create_index("ix_financial_stress_event_date", "financial_stress_event", ["date"])
    op.create_index("ix_financial_stress_event_stress_event_id", "financial_stress_event", ["stress_event_id"], unique=True)
    
    op.create_table(
        "financial_stress_summary",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("financial_summary_id", sa.String(32), unique=True, nullable=False),
        sa.Column("month", sa.String(7), nullable=False),  # YYYY-MM format
        sa.Column("triggered_indicators", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("patterns", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("recommendations_to_self", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_financial_stress_summary_month", "financial_stress_summary", ["month"], unique=True)
    op.create_index("ix_financial_stress_summary_financial_summary_id", "financial_stress_summary", ["financial_summary_id"], unique=True)
    
    # =========================================================================
    # PACK SU: Personal Safety & Risk Mitigation Planner
    # =========================================================================
    
    op.create_table(
        "safety_category",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("safety_category_id", sa.String(32), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_safety_category_safety_category_id", "safety_category", ["safety_category_id"], unique=True)
    
    op.create_table(
        "safety_checklist",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("safety_checklist_id", sa.String(32), unique=True, nullable=False),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("safety_category.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item", sa.String(255), nullable=False),
        sa.Column("frequency", sa.String(32), nullable=False),  # daily, weekly, before_travel, as_needed
        sa.Column("notes", sa.Text),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),  # active, retired
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_safety_checklist_category_id", "safety_checklist", ["category_id"])
    op.create_index("ix_safety_checklist_safety_checklist_id", "safety_checklist", ["safety_checklist_id"], unique=True)
    
    op.create_table(
        "safety_plan",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("safety_plan_id", sa.String(32), unique=True, nullable=False),
        sa.Column("situation", sa.String(255), nullable=False),
        sa.Column("steps", sa.JSON, nullable=False, server_default="[]"),  # [{step: str, order: int}, ...]
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_safety_plan_safety_plan_id", "safety_plan", ["safety_plan_id"], unique=True)
    
    op.create_table(
        "safety_event_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("safety_event_log_id", sa.String(32), unique=True, nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("safety_category.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event", sa.String(255), nullable=False),
        sa.Column("resolution_notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_safety_event_log_category_id", "safety_event_log", ["category_id"])
    op.create_index("ix_safety_event_log_date", "safety_event_log", ["date"])
    op.create_index("ix_safety_event_log_safety_event_log_id", "safety_event_log", ["safety_event_log_id"], unique=True)
    
    # =========================================================================
    # PACK SV: Empire Growth Navigator
    # =========================================================================
    
    op.create_table(
        "empire_goal",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("empire_goal_id", sa.String(32), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),  # finance, business, family, skills, real_estate, automation
        sa.Column("description", sa.Text),
        sa.Column("timeframe", sa.String(16), nullable=False),  # short_term, mid_term, long_term
        sa.Column("status", sa.String(16), nullable=False, server_default="not_started"),  # not_started, in_progress, completed, paused
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_empire_goal_category", "empire_goal", ["category"])
    op.create_index("ix_empire_goal_status", "empire_goal", ["status"])
    op.create_index("ix_empire_goal_empire_goal_id", "empire_goal", ["empire_goal_id"], unique=True)
    
    op.create_table(
        "goal_milestone",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("milestone_id", sa.String(32), unique=True, nullable=False),
        sa.Column("goal_id", sa.Integer, sa.ForeignKey("empire_goal.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("due_date", sa.Date),
        sa.Column("progress", sa.Float, nullable=False, server_default="0.0"),  # 0.0-1.0
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_goal_milestone_goal_id", "goal_milestone", ["goal_id"])
    op.create_index("ix_goal_milestone_milestone_id", "goal_milestone", ["milestone_id"], unique=True)
    
    op.create_table(
        "action_step",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("step_id", sa.String(32), unique=True, nullable=False),
        sa.Column("milestone_id", sa.Integer, sa.ForeignKey("goal_milestone.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("priority", sa.Integer, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),  # pending, in_progress, done
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_action_step_milestone_id", "action_step", ["milestone_id"])
    op.create_index("ix_action_step_step_id", "action_step", ["step_id"], unique=True)


def downgrade():
    # Drop in reverse order of creation
    op.drop_table("action_step")
    op.drop_table("goal_milestone")
    op.drop_table("empire_goal")
    
    op.drop_table("safety_event_log")
    op.drop_table("safety_plan")
    op.drop_table("safety_checklist")
    op.drop_table("safety_category")
    
    op.drop_table("financial_stress_summary")
    op.drop_table("financial_stress_event")
    op.drop_table("financial_indicator")
