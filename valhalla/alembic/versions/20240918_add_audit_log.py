"""
Alembic migration for audit_logs table
"""

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, index=True),
        sa.Column(
            "actor_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), index=True
        ),
        sa.Column("action", sa.String, nullable=False),
        sa.Column("entity", sa.String, nullable=False),
        sa.Column("entity_id", sa.String),
        sa.Column("request_id", sa.String, index=True),
        sa.Column("route", sa.String),
        sa.Column("ip", sa.String),
        sa.Column("user_agent", sa.String),
        sa.Column("before", sa.JSON),
        sa.Column("after", sa.JSON),
        sa.Column("meta", sa.JSON),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
    )
    op.create_index("ix_audit_entity_when", "audit_logs", ["entity", "created_at"])


def downgrade():
    op.drop_index("ix_audit_entity_when", table_name="audit_logs")
    op.drop_table("audit_logs")
