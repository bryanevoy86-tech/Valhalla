"""add shield events table

Revision ID: 78_shield_events_table
Revises: 77_legacies_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa

revision = "78_shield_events_table"
down_revision = "77_legacies_table"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "shield_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), server_default="low"),
        sa.Column("description", sa.String()),
        sa.Column("resolved", sa.String(), server_default="pending"),
        sa.Column("created_at", sa.DateTime())
    )

def downgrade():
    op.drop_table("shield_events")
