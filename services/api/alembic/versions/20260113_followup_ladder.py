"""followup ladder

Revision ID: 20260113_followup_ladder
Revises: 20260113_market_policy
"""
from alembic import op
import sqlalchemy as sa

revision = "20260113_followup_ladder"
down_revision = "20260113_market_policy"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "followup_task",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.String(), nullable=True),
        sa.Column("province", sa.String(), nullable=True),
        sa.Column("market", sa.String(), nullable=True),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("step", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("due_at", sa.DateTime(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("owner", sa.String(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_followup_due_completed", "followup_task", ["due_at", "completed"])

def downgrade():
    op.drop_index("ix_followup_due_completed", table_name="followup_task")
    op.drop_table("followup_task")
