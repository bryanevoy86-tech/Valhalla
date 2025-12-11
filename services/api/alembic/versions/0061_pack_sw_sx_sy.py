"""PACK SW, SX, SY: Life Timeline, Emotional Stability, Strategic Decisions

Revision ID: 0061_pack_sw_sx_sy
Revises: 0060_pack_st_su_sv
Create Date: 2025-12-07

PACK SW - Life Timeline & Major Milestones Engine
  - LifeEvent: Major life events with factual description and user-defined impact (1-5)
  - LifeMilestone: Specific milestones within events (start/finish/transition/achievement)
  - LifeTimelineSnapshot: Periodic snapshots of events, changes, and upcoming milestones

PACK SX - Emotional Neutrality & Stability Log (Safe, Non-Psych, User Input Only)
  - EmotionalStateEntry: User-stated mood, energy (1-10), cognitive load (1-10), context
  - StabilityLog: Daily events, stress factors, relief actions (user-entered, no analysis)
  - NeutralSummary: Weekly compilation of states with user interpretation only

PACK SY - Strategic Decision History & Reason Archive
  - StrategicDecision: Recorded decisions with reasoning, alternatives, constraints, status
  - DecisionRevision: Revisions when decisions change direction or are reversed
  - DecisionChainSnapshot: Snapshots of major decisions, evolution, and system impacts
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0061_pack_sw_sx_sy"
down_revision = "0060_pack_st_su_sv"
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # PACK SW: Life Timeline & Major Milestones Engine
    # =========================================================================
    
    op.create_table(
        "life_event",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.String(32), unique=True, nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),  # personal, family, business, financial, health, achievement
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("impact_level", sa.Integer, nullable=False, server_default="1"),  # 1-5
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_life_event_category", "life_event", ["category"])
    op.create_index("ix_life_event_date", "life_event", ["date"])
    op.create_index("ix_life_event_event_id", "life_event", ["event_id"], unique=True)
    
    op.create_table(
        "life_milestone",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("milestone_id", sa.String(32), unique=True, nullable=False),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("life_event.id", ondelete="CASCADE"), nullable=False),
        sa.Column("milestone_type", sa.String(32), nullable=False),  # start, finish, transition, achievement
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_life_milestone_event_id", "life_milestone", ["event_id"])
    op.create_index("ix_life_milestone_milestone_id", "life_milestone", ["milestone_id"], unique=True)
    
    op.create_table(
        "life_timeline_snapshot",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("snapshot_id", sa.String(32), unique=True, nullable=False),
        sa.Column("date_generated", sa.Date, nullable=False),
        sa.Column("major_events", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("recent_changes", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("upcoming_milestones", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("user_notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_life_timeline_snapshot_snapshot_id", "life_timeline_snapshot", ["snapshot_id"], unique=True)
    
    # =========================================================================
    # PACK SX: Emotional Neutrality & Stability Log
    # =========================================================================
    
    op.create_table(
        "emotional_state_entry",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("entry_id", sa.String(32), unique=True, nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("self_reported_mood", sa.String(255), nullable=False),
        sa.Column("energy_level", sa.Integer, nullable=False),  # 1-10
        sa.Column("cognitive_load", sa.Integer, nullable=False),  # 1-10
        sa.Column("context", sa.Text, nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_emotional_state_entry_date", "emotional_state_entry", ["date"])
    op.create_index("ix_emotional_state_entry_entry_id", "emotional_state_entry", ["entry_id"], unique=True)
    
    op.create_table(
        "stability_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("log_id", sa.String(32), unique=True, nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("events_today", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("stress_factors", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("relief_actions", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_stability_log_date", "stability_log", ["date"])
    op.create_index("ix_stability_log_log_id", "stability_log", ["log_id"], unique=True)
    
    op.create_table(
        "neutral_summary",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("summary_id", sa.String(32), unique=True, nullable=False),
        sa.Column("week_of", sa.String(10), nullable=False),  # YYYY-WXX
        sa.Column("average_energy", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("task_load", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("user_highlights", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("user_defined_interpretation", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_neutral_summary_week_of", "neutral_summary", ["week_of"])
    op.create_index("ix_neutral_summary_summary_id", "neutral_summary", ["summary_id"], unique=True)
    
    # =========================================================================
    # PACK SY: Strategic Decision History & Reason Archive
    # =========================================================================
    
    op.create_table(
        "strategic_decision",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("decision_id", sa.String(32), unique=True, nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),  # business, family, finance, real_estate, system
        sa.Column("reasoning", sa.Text, nullable=False),
        sa.Column("alternatives_considered", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("constraints", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("expected_outcome", sa.Text, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),  # active, revised, reversed, completed
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_strategic_decision_category", "strategic_decision", ["category"])
    op.create_index("ix_strategic_decision_status", "strategic_decision", ["status"])
    op.create_index("ix_strategic_decision_decision_id", "strategic_decision", ["decision_id"], unique=True)
    
    op.create_table(
        "decision_revision",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("revision_id", sa.String(32), unique=True, nullable=False),
        sa.Column("decision_id", sa.Integer, sa.ForeignKey("strategic_decision.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("reason_for_revision", sa.Text, nullable=False),
        sa.Column("what_changed", sa.Text, nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_decision_revision_decision_id", "decision_revision", ["decision_id"])
    op.create_index("ix_decision_revision_revision_id", "decision_revision", ["revision_id"], unique=True)
    
    op.create_table(
        "decision_chain_snapshot",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("snapshot_id", sa.String(32), unique=True, nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("major_decisions", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("revisions", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("reasons", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("system_impacts", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_decision_chain_snapshot_snapshot_id", "decision_chain_snapshot", ["snapshot_id"], unique=True)


def downgrade():
    # Drop in reverse order of creation
    op.drop_table("decision_chain_snapshot")
    op.drop_table("decision_revision")
    op.drop_table("strategic_decision")
    
    op.drop_table("neutral_summary")
    op.drop_table("stability_log")
    op.drop_table("emotional_state_entry")
    
    op.drop_table("life_timeline_snapshot")
    op.drop_table("life_milestone")
    op.drop_table("life_event")
