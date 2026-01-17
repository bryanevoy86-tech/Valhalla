"""PACK-CORE-PRELAUNCH-01 through 12 - Heimdall Launch & Ops Core + Safeguards

Creates 13 core operational tables:
- alerts: Central alert management (RED/YELLOW/GREEN levels, multi-domain)
- daily_snapshots: Morning briefing snapshots with financial/risk summary
- nightly_snapshots: Nightly shutdown snapshots with completion tracking
- scenarios: Crisis/opportunity scenarios with trigger & action conditions
- system_events: Unified event log with 11 event types
- safeguard_rules: Risk mitigation rules (FREEZE/SLOW/FAST_TRACK)
- preference_profiles: User preferences (directness, empathy, task management)
- automation_jobs: Job scheduler with status tracking
- boot_logs: System startup sequence validation
- behavior_profiles: Human alignment profiling (lawyers, accountants, contractors, partners)
- eia_status: EIA compliance monitoring and risk tracking
- arbitrage_settings: Arbitrage trading mode and bankroll protection
- brrrr_stability: BRRRR property stability evaluation
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.engine.reflection import Inspector

revision = "pack_core_prelaunch_01"
down_revision = "0114"
branch_labels = None
depends_on = None


def _table_exists(conn, name: str) -> bool:
    """Check if table exists."""
    insp = Inspector.from_engine(conn)
    return name in insp.get_table_names()


def upgrade() -> None:
    """Create PACK-CORE-PRELAUNCH-01 tables."""
    bind = op.get_bind()

    # 1. Alerts table
    if not _table_exists(bind, "alerts"):
        op.create_table(
            "alerts",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
            sa.Column("level", sa.String(50), nullable=False),  # AlertLevel: RED, YELLOW, GREEN
            sa.Column("domain", sa.String(50), nullable=False),  # AlertDomain: FINANCE, BRRRR, ARBITRAGE, etc.
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("alert_metadata", JSONB(), nullable=True),
            sa.Column("status", sa.String(50), nullable=False, server_default="OPEN"),  # OPEN, ACKNOWLEDGED, RESOLVED
            sa.Column("source", sa.String(100), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_alerts_created_at", "alerts", ["created_at"])
        op.create_index("ix_alerts_level", "alerts", ["level"])
        op.create_index("ix_alerts_domain", "alerts", ["domain"])
        op.create_index("ix_alerts_status", "alerts", ["status"])

    # 2. Daily Snapshots table
    if not _table_exists(bind, "daily_snapshots"):
        op.create_table(
            "daily_snapshots",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
            sa.Column("snapshot_date", sa.Date(), nullable=False),
            sa.Column("financial_summary", JSONB(), nullable=True),
            sa.Column("risk_summary", JSONB(), nullable=True),
            sa.Column("tasks_today", sa.Integer(), nullable=True),
            sa.Column("alerts_summary", JSONB(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_daily_snapshots_created_at", "daily_snapshots", ["created_at"])
        op.create_index("ix_daily_snapshots_snapshot_date", "daily_snapshots", ["snapshot_date"])

    # 3. Nightly Snapshots table
    if not _table_exists(bind, "nightly_snapshots"):
        op.create_table(
            "nightly_snapshots",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
            sa.Column("snapshot_date", sa.Date(), nullable=False),
            sa.Column("completed_tasks", sa.Integer(), nullable=True),
            sa.Column("missed_tasks", sa.Integer(), nullable=True),
            sa.Column("projection_changes", JSONB(), nullable=True),
            sa.Column("risk_changes", JSONB(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_nightly_snapshots_created_at", "nightly_snapshots", ["created_at"])
        op.create_index("ix_nightly_snapshots_snapshot_date", "nightly_snapshots", ["snapshot_date"])

    # 4. Scenarios table
    if not _table_exists(bind, "scenarios"):
        op.create_table(
            "scenarios",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
            sa.Column("code", sa.String(100), unique=True, nullable=False),
            sa.Column("category", sa.String(50), nullable=False),  # ScenarioCategory
            sa.Column("severity", sa.String(50), nullable=False),  # ScenarioSeverity: LOW, MEDIUM, HIGH, CRITICAL
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("trigger_conditions", JSONB(), nullable=True),
            sa.Column("recommended_actions", JSONB(), nullable=True),
            sa.Column("fallback_actions", JSONB(), nullable=True),
            sa.Column("auto_actions", JSONB(), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )
        op.create_index("ix_scenarios_created_at", "scenarios", ["created_at"])
        op.create_index("ix_scenarios_code", "scenarios", ["code"])
        op.create_index("ix_scenarios_category", "scenarios", ["category"])

    # 5. System Events table (Unified Log)
    if not _table_exists(bind, "system_events"):
        op.create_table(
            "system_events",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
            sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("event_type", sa.String(50), nullable=False),  # EventType: ACTION, AUTO, RISK, FINANCE, etc.
            sa.Column("source", sa.String(100), nullable=True),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("data", JSONB(), nullable=True),
            sa.Column("correlation_id", sa.String(100), nullable=True),
        )
        op.create_index("ix_system_events_timestamp", "system_events", ["timestamp"])
        op.create_index("ix_system_events_event_type", "system_events", ["event_type"])
        op.create_index("ix_system_events_source", "system_events", ["source"])
        op.create_index("ix_system_events_correlation_id", "system_events", ["correlation_id"])

    # 6. Safeguard Rules table
    if not _table_exists(bind, "safeguard_rules"):
        op.create_table(
            "safeguard_rules",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("category", sa.String(50), nullable=False),  # SafeguardCategory: FREEZE, SLOW, FAST_TRACK
            sa.Column("domain", sa.String(50), nullable=False),  # SafeguardDomain: EIA, ARBITRAGE, BRRRR, etc.
            sa.Column("condition_definition", JSONB(), nullable=False),
            sa.Column("effect_definition", JSONB(), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )
        op.create_index("ix_safeguard_rules_created_at", "safeguard_rules", ["created_at"])
        op.create_index("ix_safeguard_rules_category", "safeguard_rules", ["category"])
        op.create_index("ix_safeguard_rules_domain", "safeguard_rules", ["domain"])

    # 7. Preference Profiles table
    if not _table_exists(bind, "preference_profiles"):
        op.create_table(
            "preference_profiles",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
            sa.Column("user_id", sa.String(100), unique=True, nullable=False),
            sa.Column("directness", sa.Integer(), nullable=False, server_default="5"),  # 1-10 scale
            sa.Column("empathy_weight", sa.Integer(), nullable=False, server_default="5"),  # 1-10 scale
            sa.Column("detail_level", sa.String(50), nullable=False, server_default="MEDIUM"),  # DetailLevel: LOW, MEDIUM, HIGH
            sa.Column("push_level", sa.Integer(), nullable=False, server_default="5"),  # 1-10 scale
            sa.Column("show_alternatives", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("max_concurrent_tasks", sa.Integer(), nullable=False, server_default="5"),
            sa.Column("overwhelm_response", sa.String(50), nullable=False, server_default="SIMPLIFY"),  # OverwhelmResponse
            sa.Column("preferred_morning_time", sa.String(50), nullable=True),  # HH:MM format
            sa.Column("preferred_night_time", sa.String(50), nullable=True),  # HH:MM format
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )
        op.create_index("ix_preference_profiles_user_id", "preference_profiles", ["user_id"])
        op.create_index("ix_preference_profiles_created_at", "preference_profiles", ["created_at"])

    # 8. Automation Jobs table
    if not _table_exists(bind, "automation_jobs"):
        op.create_table(
            "automation_jobs",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
            sa.Column("code", sa.String(100), unique=True, nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("schedule", sa.String(100), nullable=True),  # Cron-style schedule
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_status", sa.String(50), nullable=True),  # SUCCESS, FAILED, PARTIAL
            sa.Column("last_result", JSONB(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )
        op.create_index("ix_automation_jobs_created_at", "automation_jobs", ["created_at"])
        op.create_index("ix_automation_jobs_code", "automation_jobs", ["code"])
        op.create_index("ix_automation_jobs_enabled", "automation_jobs", ["enabled"])

    # 9. Boot Logs table
    if not _table_exists(bind, "boot_logs"):
        op.create_table(
            "boot_logs",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
            sa.Column("run_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("status", sa.String(50), nullable=False),  # BootStatus: SUCCESS, PARTIAL, FAILED
            sa.Column("steps", JSONB(), nullable=True),  # Array of {name, status, message}
        )
        op.create_index("ix_boot_logs_run_at", "boot_logs", ["run_at"])
        op.create_index("ix_boot_logs_status", "boot_logs", ["status"])

    # 10. Behavior Profiles table (PACK-PRELAUNCH-09)
    if not _table_exists(bind, "behavior_profiles"):
        op.create_table(
            "behavior_profiles",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("role", sa.String(64), nullable=True),  # lawyer, accountant, contractor, partner, etc.
            sa.Column("public_data", JSONB(), nullable=True),
            sa.Column("alignment_score", sa.Float(), nullable=False),  # 0-100
            sa.Column("risk_score", sa.Float(), nullable=False),  # 0-100
            sa.Column("recommended_style", JSONB(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_behavior_profiles_role", "behavior_profiles", ["role"])
        op.create_index("ix_behavior_profiles_created_at", "behavior_profiles", ["created_at"])

    # 11. EIA Status table (PACK-PRELAUNCH-10)
    if not _table_exists(bind, "eia_status"):
        op.create_table(
            "eia_status",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
            sa.Column("monthly_limit", sa.Float(), nullable=False),
            sa.Column("current_income", sa.Float(), nullable=False),
            sa.Column("projected_income", sa.Float(), nullable=False),
            sa.Column("risk_level", sa.String(32), nullable=False),  # RED, YELLOW, GREEN
            sa.Column("recommendations", JSONB(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_eia_status_updated_at", "eia_status", ["updated_at"])

    # 12. Arbitrage Settings table (PACK-PRELAUNCH-11)
    if not _table_exists(bind, "arbitrage_settings"):
        op.create_table(
            "arbitrage_settings",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
            sa.Column("mode", sa.String(32), nullable=False, server_default="SAFE"),  # SAFE, NORMAL, AGGRESSIVE
            sa.Column("bankroll", sa.Float(), nullable=False),
            sa.Column("max_daily_risk", sa.Float(), nullable=False),
            sa.Column("max_monthly_risk", sa.Float(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_arbitrage_settings_updated_at", "arbitrage_settings", ["updated_at"])

    # 13. BRRRR Stability table (PACK-PRELAUNCH-12)
    if not _table_exists(bind, "brrrr_stability"):
        op.create_table(
            "brrrr_stability",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
            sa.Column("property_address", sa.String(255), nullable=False),
            sa.Column("stability_score", sa.Float(), nullable=False),  # 0-100
            sa.Column("risk_factors", JSONB(), nullable=True),
            sa.Column("recommendations", JSONB(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_brrrr_stability_updated_at", "brrrr_stability", ["updated_at"])
        op.create_index("ix_brrrr_stability_property_address", "brrrr_stability", ["property_address"])


def downgrade() -> None:
    """Drop PACK-CORE-PRELAUNCH-01 through 12 tables."""
    bind = op.get_bind()

    # Drop in reverse order of creation
    tables = [
        "brrrr_stability",
        "arbitrage_settings",
        "eia_status",
        "behavior_profiles",
        "boot_logs",
        "automation_jobs",
        "preference_profiles",
        "safeguard_rules",
        "system_events",
        "scenarios",
        "nightly_snapshots",
        "daily_snapshots",
        "alerts",
    ]

    for table_name in tables:
        if _table_exists(bind, table_name):
            # Drop indexes first
            op.drop_index(f"ix_{table_name}_run_at", table_name=table_name, if_exists=True)
            op.drop_index(f"ix_{table_name}_status", table_name=table_name, if_exists=True)
            op.drop_index(f"ix_{table_name}_created_at", table_name=table_name, if_exists=True)
            op.drop_index(f"ix_{table_name}_updated_at", table_name=table_name, if_exists=True)
            op.drop_index(f"ix_{table_name}_level", table_name=table_name, if_exists=True)
            op.drop_index(f"ix_{table_name}_domain", table_name=table_name, if_exists=True)
            op.drop_index(f"ix_{table_name}_category", table_name=table_name, if_exists=True)
            op.drop_index(f"ix_{table_name}_snapshot_date", table_name=table_name, if_exists=True)
            op.drop_index(f"ix_{table_name}_event_type", table_name=table_name, if_exists=True)
            op.drop_index(f"ix_{table_name}_source", table_name=table_name, if_exists=True)
            op.drop_index(f"ix_{table_name}_correlation_id", table_name=table_name, if_exists=True)
            op.drop_index(f"ix_{table_name}_code", table_name=table_name, if_exists=True)
            op.drop_index(f"ix_{table_name}_user_id", table_name=table_name, if_exists=True)
            op.drop_index(f"ix_{table_name}_enabled", table_name=table_name, if_exists=True)
            op.drop_index(f"ix_{table_name}_role", table_name=table_name, if_exists=True)
            op.drop_index(f"ix_{table_name}_property_address", table_name=table_name, if_exists=True)
            
            # Drop table
            op.drop_table(table_name)
