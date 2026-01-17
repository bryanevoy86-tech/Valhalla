"""0075 pack ug notifications

Revision ID: 0075
Revises: 0074
Create Date: 2024-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0075"
down_revision = "0074"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_channels",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("name", sa.String(256), nullable=False, unique=True),
        sa.Column("channel_type", sa.String(64), nullable=False),
        sa.Column("target", sa.String(512), nullable=False),
        sa.Column("active", sa.Boolean(), default=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_notification_channels_active", "notification_channels", ["active"])

    op.create_table(
        "notification_outbox",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("notification_channels.id"), nullable=False),
        sa.Column("subject", sa.String(512), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(32), default="pending", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), default=0, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_notification_outbox_status", "notification_outbox", ["status"])
    op.create_index("idx_notification_outbox_created", "notification_outbox", ["created_at"])


def downgrade() -> None:
    op.drop_table("notification_outbox")
    op.drop_table("notification_channels")
