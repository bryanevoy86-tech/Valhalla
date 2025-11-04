import sqlalchemy as sa
from alembic import op

revision = "add_core_chunks"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # --- Funfund (Chunk 32) ---
    op.create_table(
        "funding_requests",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, index=True, nullable=False),
        sa.Column(
            "legacy_id",
            sa.Integer,
            sa.ForeignKey("legacies.id", ondelete="SET NULL"),
            index=True,
            nullable=True,
        ),
        sa.Column(
            "requested_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            index=True,
            nullable=True,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String, nullable=False, server_default="USD"),
        sa.Column("purpose", sa.String, nullable=True),
        sa.Column("status", sa.String, nullable=False, server_default="draft"),
        sa.Column("meta", sa.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )
    op.create_table(
        "funding_approvals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "request_id",
            sa.Integer,
            sa.ForeignKey("funding_requests.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column(
            "approver_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            index=True,
            nullable=True,
        ),
        sa.Column("decision", sa.String, nullable=False),
        sa.Column("note", sa.String, nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )
    op.create_table(
        "disbursements",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, index=True, nullable=False),
        sa.Column(
            "request_id",
            sa.Integer,
            sa.ForeignKey("funding_requests.id", ondelete="SET NULL"),
            index=True,
            nullable=True,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String, nullable=False, server_default="USD"),
        sa.Column("method", sa.String, nullable=True),
        sa.Column("reference", sa.String, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
    )
    op.create_table(
        "repayments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, index=True, nullable=False),
        sa.Column(
            "request_id",
            sa.Integer,
            sa.ForeignKey("funding_requests.id", ondelete="SET NULL"),
            index=True,
            nullable=True,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String, nullable=False, server_default="USD"),
        sa.Column("method", sa.String, nullable=True),
        sa.Column("reference", sa.String, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
    )
    op.create_table(
        "repayment_schedules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, index=True, nullable=False),
        sa.Column(
            "request_id",
            sa.Integer,
            sa.ForeignKey("funding_requests.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column("schedule", sa.JSON, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="active"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )
    # --- Shield (Chunk 31) ---
    op.create_table(
        "ip_rules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, index=True, nullable=True),
        sa.Column("label", sa.String, nullable=True),
        sa.Column("cidr", sa.String, nullable=False),
        sa.Column("action", sa.String, nullable=False, server_default="allow"),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, index=True, nullable=True),
        sa.Column("user_id", sa.Integer, index=True, nullable=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("prefix", sa.String, nullable=False, index=True),
        sa.Column("hash", sa.String, nullable=False),
        sa.Column("scopes", sa.JSON, nullable=True),
        sa.Column("active", sa.Boolean, server_default=sa.text("1"), index=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )
    op.create_table(
        "rate_limits",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key", sa.String, nullable=False, index=True),
        sa.Column("window_sec", sa.Integer, nullable=False),
        sa.Column("max_hits", sa.Integer, nullable=False),
        sa.Column("active", sa.Boolean, server_default=sa.text("1"), index=True),
        sa.Column("note", sa.String, nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )
    op.create_table(
        "request_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "ts",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
        sa.Column("ip", sa.String, index=True),
        sa.Column("user_id", sa.Integer, index=True, nullable=True),
        sa.Column("org_id", sa.Integer, index=True, nullable=True),
        sa.Column("route", sa.String, index=True),
        sa.Column("method", sa.String),
        sa.Column("status", sa.Integer),
        sa.Column("meta", sa.JSON),
    )
    # --- Multi-tenant (Chunk 24) ---
    op.create_table(
        "orgs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(128), nullable=False),
    )
    op.create_table(
        "org_members",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "org_id",
            sa.Integer,
            sa.ForeignKey("orgs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("role", sa.String(16), nullable=False, server_default="member"),
        sa.UniqueConstraint("org_id", "user_id", name="uq_org_user"),
    )
    with op.batch_alter_table("legacies", schema=None) as batch:
        try:
            batch.add_column(
                sa.Column(
                    "org_id", sa.Integer, sa.ForeignKey("orgs.id", ondelete="CASCADE"), index=True
                )
            )
        except Exception:
            pass
    if not op.get_bind().dialect.has_table(op.get_bind(), "deals"):
        op.create_table(
            "deals",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("org_id", sa.Integer, nullable=False, index=True),
            sa.Column(
                "legacy_id",
                sa.Integer,
                sa.ForeignKey("legacies.id", ondelete="SET NULL"),
                index=True,
            ),
            sa.Column("status", sa.String, nullable=False, server_default="draft"),
            sa.Column("city", sa.String),
            sa.Column("state", sa.String),
            sa.Column("price", sa.Numeric(12, 2)),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                index=True,
            ),
        )
    with op.batch_alter_table("users", schema=None) as batch:
        try:
            batch.add_column(sa.Column("stripe_customer_id", sa.String(64)))
        except Exception:
            pass
        try:
            batch.add_column(sa.Column("plan_key", sa.String(32), server_default="starter_monthly"))
        except Exception:
            pass
    # --- Notifications & Webhooks (Chunk 25) ---
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, sa.ForeignKey("orgs.id", ondelete="CASCADE"), index=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("channel", sa.String(32), nullable=False, server_default="in-app"),
        sa.Column("topic", sa.String(64), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("body", sa.Text),
        sa.Column("meta", sa.JSON),
        sa.Column("unread", sa.Boolean, server_default=sa.text("1"), index=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
    )
    op.create_table(
        "user_notif_prefs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True
        ),
        sa.Column("topics", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
    )
    op.create_table(
        "webhook_endpoints",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "org_id",
            sa.Integer,
            sa.ForeignKey("orgs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("description", sa.String(256)),
        sa.Column("secret", sa.String(128), nullable=False),
        sa.Column("active", sa.Boolean, server_default=sa.text("1")),
        sa.Column("topics", sa.JSON),
    )
    op.create_table(
        "outbound_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, index=True),
        sa.Column("topic", sa.String(128), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
    )
    # --- Alerts & Schedules (Chunk 26) ---
    op.create_table(
        "schedules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, sa.ForeignKey("orgs.id", ondelete="CASCADE"), index=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("kind", sa.String, nullable=False, server_default="interval"),
        sa.Column("spec", sa.JSON, nullable=False),
        sa.Column("task", sa.String, nullable=False),
        sa.Column("params", sa.JSON),
        sa.Column("next_run_at", sa.TIMESTAMP(timezone=True), index=True),
        sa.Column("active", sa.Boolean, server_default=sa.text("1"), index=True),
        sa.Column("last_error", sa.Text),
    )
    op.create_table(
        "alert_rules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "org_id",
            sa.Integer,
            sa.ForeignKey("orgs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("condition", sa.JSON, nullable=False),
        sa.Column("severity", sa.String, nullable=False, server_default="warn"),
        sa.Column("channels", sa.JSON, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("dedupe_key", sa.String),
        sa.Column("active", sa.Boolean, server_default=sa.text("1"), index=True),
    )
    op.create_table(
        "alert_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, nullable=False, index=True),
        sa.Column(
            "rule_id", sa.Integer, sa.ForeignKey("alert_rules.id", ondelete="SET NULL"), index=True
        ),
        sa.Column(
            "fired_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
        sa.Column("payload", sa.JSON),
        sa.Column("severity", sa.String, nullable=False, server_default="warn"),
        sa.Column("dedupe_key", sa.String),
    )
    op.create_table(
        "sla_timers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, nullable=False, index=True),
        sa.Column("resource", sa.String, nullable=False),
        sa.Column("due_at", sa.TIMESTAMP(timezone=True), nullable=False, index=True),
        sa.Column("status", sa.String, nullable=False, server_default="open"),
        sa.Column("rule", sa.String),
        sa.Column("meta", sa.JSON),
    )
    # --- Import/Export (Chunk 27) ---
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, nullable=False, index=True),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="queued"),
        sa.Column("src_filename", sa.String(256), nullable=False),
        sa.Column("options", sa.JSON),
        sa.Column("total_rows", sa.Integer),
        sa.Column("success_rows", sa.Integer, server_default="0"),
        sa.Column("error_rows", sa.Integer, server_default="0"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("error_message", sa.Text),
    )
    op.create_table(
        "import_row_errors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "job_id", sa.Integer, sa.ForeignKey("import_jobs.id", ondelete="CASCADE"), index=True
        ),
        sa.Column("row_number", sa.Integer, nullable=False),
        sa.Column("data", sa.JSON),
        sa.Column("error", sa.Text, nullable=False),
    )
    op.create_table(
        "export_jobs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, nullable=False, index=True),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="queued"),
        sa.Column("filters", sa.JSON),
        sa.Column("out_filename", sa.String(256)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("error_message", sa.Text),
    )
    # --- Search/Saved Views (Chunk 28) ---
    op.create_table(
        "saved_views",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, nullable=False, index=True),
        sa.Column("user_id", sa.Integer, nullable=False, index=True),
        sa.Column("entity", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("query", sa.JSON, nullable=False),
        sa.Column("shared", sa.Boolean, server_default=sa.text("0"), index=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )
    op.create_table(
        "recent_searches",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, nullable=False, index=True),
        sa.Column("user_id", sa.Integer, nullable=False, index=True),
        sa.Column("entity", sa.String(32), nullable=False),
        sa.Column("query", sa.JSON, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
    )
    # --- Reporting (Chunk 29) ---
    op.create_table(
        "saved_charts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, nullable=False, index=True),
        sa.Column("user_id", sa.Integer, nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("viz", sa.String(16), nullable=False, server_default="line"),
        sa.Column("spec", sa.JSON, nullable=False),
        sa.Column("shared", sa.Boolean, server_default=sa.text("0"), index=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )
    op.create_table(
        "dashboards",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, nullable=False, index=True),
        sa.Column("user_id", sa.Integer, nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("layout", sa.JSON, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("shared", sa.Boolean, server_default=sa.text("0"), index=True),
    )
    # --- Admin Console (Chunk 30) ---
    op.create_table(
        "feature_flags",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("scope", sa.String, nullable=False, server_default="global"),
        sa.Column("key", sa.String, nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("payload", sa.JSON),
        sa.Column("org_id", sa.Integer, sa.ForeignKey("orgs.id", ondelete="CASCADE"), index=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), index=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )
    op.create_index("ix_feature_flags_key_scope", "feature_flags", ["key", "scope"])
    op.create_table(
        "admin_actions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "actor_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), index=True
        ),
        sa.Column("org_id", sa.Integer, sa.ForeignKey("orgs.id", ondelete="SET NULL"), index=True),
        sa.Column("action", sa.String, nullable=False),
        sa.Column("details", sa.JSON),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
    )


def downgrade():
    for t in [
        "dashboards",
        "saved_charts",
        "recent_searches",
        "saved_views",
        "export_jobs",
        "import_row_errors",
        "import_jobs",
        "sla_timers",
        "alert_events",
        "alert_rules",
        "schedules",
        "outbound_events",
        "webhook_endpoints",
        "user_notif_prefs",
        "notifications",
        "deals",
        "org_members",
        "orgs",
    ]:
        try:
            op.drop_table(t)
        except Exception:
            pass
