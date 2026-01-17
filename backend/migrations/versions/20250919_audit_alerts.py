"""
Alembic migration for audit_events and security_alerts tables (Chunk 45)
"""

import sqlalchemy as sa
from alembic import op

revision = "20250919_audit_alerts"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("org_id", sa.BigInteger, nullable=False),
        sa.Column("user_id", sa.BigInteger),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("resource", sa.Text),
        sa.Column("metadata", sa.JSON),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index(
        "idx_audit_events_org_time", "audit_events", ["org_id", "created_at"], unique=False
    )
    op.create_index(
        "idx_audit_events_action_time", "audit_events", ["action", "created_at"], unique=False
    )

    op.create_table(
        "security_alerts",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("org_id", sa.BigInteger, nullable=False),
        sa.Column("kind", sa.Text, nullable=False),
        sa.Column("window_minutes", sa.Integer, nullable=False),
        sa.Column("observed_count", sa.Integer, nullable=False),
        sa.Column("threshold", sa.Integer, nullable=False),
        sa.Column("sample", sa.JSON),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("sent", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
    )
    op.create_index(
        "idx_security_alerts_org_time", "security_alerts", ["org_id", "created_at"], unique=False
    )


def downgrade():
    op.drop_index("idx_audit_events_org_time", table_name="audit_events")
    op.drop_index("idx_audit_events_action_time", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("idx_security_alerts_org_time", table_name="security_alerts")
    op.drop_table("security_alerts")
