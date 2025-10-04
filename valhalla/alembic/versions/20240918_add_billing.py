"""
Alembic migration for Stripe billing tables
"""

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, index=True, nullable=False),
        sa.Column("stripe_subscription_id", sa.String, unique=True, index=True, nullable=False),
        sa.Column("status", sa.String, nullable=False),
        sa.Column("plan_key", sa.String),
        sa.Column("items", sa.JSON),
        sa.Column("current_period_end", sa.TIMESTAMP(timezone=True)),
        sa.Column("cancel_at_period_end", sa.Boolean, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
    )
    op.create_table(
        "seat_counters",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, unique=True, index=True, nullable=False),
        sa.Column("seats", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )
    op.create_table(
        "usage_meters",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, index=True, nullable=False),
        sa.Column("key", sa.String, index=True, nullable=False),
        sa.Column("qty", sa.Integer, nullable=False, server_default="0"),
        sa.Column("window", sa.String, nullable=False, server_default="'daily'"),
        sa.Column("last_posted_at", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )


def downgrade():
    op.drop_table("usage_meters")
    op.drop_table("seat_counters")
    op.drop_table("subscriptions")
